from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import random, datetime
# from .models import Product


class EmailOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.created_at = datetime.datetime.now()
        self.save()
        return self.otp

    from django.utils import timezone

    def is_valid(self):
        return (timezone.now() - self.created_at).total_seconds() < 600


# ===========================
# Product / Stock Model
# ===========================
class Product(models.Model):
    UNIT_CHOICES = [
        ('Units', 'Units'),
        ('Kg', 'Kilogram'),
        ('Litre', 'Litre'),
        ('Meter', 'Meter'),
        ('Pcs', 'Pieces'),
    ]

    name = models.CharField(max_length=100)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='Units')
    on_hand = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True, null=True)

    def _str_(self):
        return self.name

    # stock levels
    on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    free_to_use = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    incoming = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outgoing = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # calculated
    total_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def recalc_totals(self):
        self.total_value = self.on_hand * self.unit_cost
        if self.pk:  # Check if the instance has a primary key (i.e., it exists in the database)
            self.save(update_fields=['total_value'])
        else:
            # For new objects, the total_value will be saved during the initial save
            pass


# ===========================
# Stock Ledger Entry
# ===========================
class StockLedgerEntry(models.Model):
    MOVEMENT_TYPES = [
        ('IN', 'Incoming'),
        ('OUT', 'Outgoing'),
        ('PROD', 'Production'),
        ('CONS', 'Consumption'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ledger_entries')
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.product.name} - {self.movement_type} ({self.quantity})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        product = self.product

        if self.movement_type == 'IN':
            product.on_hand += self.quantity
            product.incoming -= min(product.incoming, self.quantity)
        elif self.movement_type == 'OUT':
            product.on_hand -= self.quantity
            product.outgoing -= min(product.outgoing, self.quantity)
        elif self.movement_type == 'PROD':
            product.on_hand += self.quantity
            product.free_to_use += self.quantity
        elif self.movement_type == 'CONS':
            product.on_hand -= self.quantity
            product.free_to_use -= min(product.free_to_use, self.quantity)

        product.recalc_totals()
        product.save()


# ===========================
# Work Center
# ===========================
class WorkCenter(models.Model):
    name = models.CharField(max_length=100, unique=True)
    cost_per_hour = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


# ===========================
# Bill of Material & Components
# ===========================
class BillofMaterials(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    unit = models.CharField(max_length=50)

class Component(models.Model):
    bom = models.ForeignKey(BillofMaterials, related_name='components', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)   # Component name
    quantity = models.PositiveIntegerField()   # Quantity required
    unit = models.CharField(max_length=50)    # e.g., "pieces", "kg"

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"
class Operation(models.Model):
    bom = models.ForeignKey(BillofMaterials, related_name='operations', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)       # e.g., "Assembly"
    time_minutes = models.PositiveIntegerField()  # Time required in minutes

    def __str__(self):
        return f"{self.name} ({self.time_minutes} mins)"

# ===========================
# Manufacturing Order
# ===========================
class ManufacturingOrder(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Confirmed', 'Confirmed'),
        ('In-Progress', 'In-Progress'),
        ('To Close', 'To Close'),
        ('Done', 'Done'),
    ]

    reference = models.CharField(max_length=20, unique=True)
    schedule_date = models.DateField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='manufacturing_orders')
    assignee = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, choices=Product.UNIT_CHOICES, default='Units')
    bom = models.ForeignKey(BillofMaterials, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.reference


class ManufacturingOrderComponent(models.Model):
    manufacturing_order = models.ForeignKey(ManufacturingOrder, on_delete=models.CASCADE, related_name='components')
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    to_consume = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.manufacturing_order.reference} - {self.component.name}"


# ===========================
# Work Order (per Manufacturing Order)
# ===========================
class WorkOrder(models.Model):
    STATUS_CHOICES = [
        ('New', 'New'),
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Done', 'Done'),
    ]

    manufacturing_order = models.ForeignKey(ManufacturingOrder, on_delete=models.CASCADE, related_name='work_orders')
    reference = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    assigned_to = models.CharField(max_length=100, blank=True, null=True)
    progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return self.reference

class WorkProduct(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=50, default="pcs")

    def __str__(self):
        return self.name
    
class Profile(models.Model):
    ROLE_CHOICES = (
        ('manager', 'Manager'),
        ('operator', 'Operator'),
        ('inventory', 'Inventory Manager'),
        ('admin', 'Admin'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    otp = models.CharField(max_length=6, blank=True, null=True)


class Component(models.Model):
    name = models.CharField(max_length=100)
    unit = models.CharField(max_length=20, default="pcs")
    total_quantity = models.IntegerField(default=0)
    used_quantity = models.IntegerField(default=0)

    @property
    def available_quantity(self):
        return self.total_quantity - self.used_quantity

    def __str__(self):
        return f"{self.name} ({self.unit})"

class ManufacturingOrderComponent(models.Model):
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    quantity = models.IntegerField()

