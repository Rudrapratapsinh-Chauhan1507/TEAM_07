from django.contrib import admin
from .models import (
    Profile,
    EmailOTP,
    Product,
    StockLedgerEntry,
    WorkCenter,
    BillofMaterials,
    Component,
    ManufacturingOrder,
    ManufacturingOrderComponent,
    WorkOrder,
)

# ==============================
# User Profile & OTP
# ==============================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "otp")
    search_fields = ("user__username", "role")


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('id',"user", "otp", "created_at")
    search_fields = ("user__username", "otp")
    list_filter = ("created_at",)


# ==============================
# Product & Stock
# ==============================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id',"name", "unit_cost", "unit", "on_hand", "free_to_use", "incoming", "outgoing", "total_value")
    search_fields = ("name",)
    list_filter = ("unit",)


@admin.register(StockLedgerEntry)
class StockLedgerEntryAdmin(admin.ModelAdmin):
    list_display = ('id',"product", "movement_type", "quantity", "reference", "timestamp")
    list_filter = ("movement_type", "timestamp")
    search_fields = ("product__name", "reference")


# ==============================
# Work Center
# ==============================
@admin.register(WorkCenter)
class WorkCenterAdmin(admin.ModelAdmin):
    list_display = ('id',"name", "cost_per_hour")
    search_fields = ("name",)


# ==============================
# Bill of Material & Components
# ==============================
@admin.register(BillofMaterials)
class BillOfMaterialAdmin(admin.ModelAdmin):
    list_display = ('id',"name", "product")
    search_fields = ("name", "product__name")


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ('id',"name", "available_quantity", "unit")
    search_fields = ("name",)


# ==============================
# Manufacturing Order & Components
# ==============================
@admin.register(ManufacturingOrder)
class ManufacturingOrderAdmin(admin.ModelAdmin):
    list_display = ('id',"reference", "schedule_date", "product", "quantity", "unit", "status", "created_at")
    list_filter = ("status", "schedule_date")
    search_fields = ("reference", "product__name")


@admin.register(ManufacturingOrderComponent)
class ManufacturingOrderComponentAdmin(admin.ModelAdmin):
    list_display = ('id', "component", "quantity")
    # search_fields = ("component")


# ==============================
# Work Order
# ==============================
@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('id',"reference", "manufacturing_order", "status", "assigned_to", "progress")
    list_filter = ("status",)
    search_fields = ("reference", "manufacturing_order__reference", "assigned_to")

class ComponentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "available_quantity", "unit")

    def available_quantity(self, obj):
        return obj.total_quantity - obj.used_quantity