from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import SignupForm, LoginForm, ForgotPasswordForm, OTPVerificationForm
from django.core.mail import send_mail
from django.conf import settings
from .models import EmailOTP
from django.core.mail import EmailMultiAlternatives
from .models import Product,BillofMaterials, Component
from .models import ManufacturingOrder, ManufacturingOrderComponent, Product, BillofMaterials, Component, User
from django.http import JsonResponse
from django.utils import timezone
from .models import StockLedgerEntry
from .forms import ProductForm
import datetime
from django.db.models import Count, Q
# from .models import BOM
from .forms import ManufacturingOrderForm 

def signup_view(request):
    if request.method == "POST":
        username = request.POST['username']
        fullname = request.POST['full_name']
        email = request.POST['email']
        password = request.POST['password']

        # 🔹 Check duplicates
        if User.objects.filter(username=username).exists():
            messages.error(request, "⚠️ Username already exists!")
            return redirect('signup')
        if User.objects.filter(email=email).exists():
            messages.error(request, "⚠️ Email already registered!")
            return redirect('signup')

        # 🔹 Create user as inactive
        user = User.objects.create_user(
            username=username,
            first_name=fullname,
            email=email,
            password=password,
            is_active=False
        )

        # 🔹 Create OTP
        otp_instance, created = EmailOTP.objects.get_or_create(user=user)
        otp = otp_instance.generate_otp()

        # 🔹 Send Email
        subject = "Verify Your Email - Work Order System"
        text_content = f"Your OTP is {otp}"
        html_content = f"""
        <html>
          <body>
            <h2 style="color:#16a34a;">🔐 Email Verification</h2>
            <p>Hello <b>{fullname}</b>,</p>
            <p>Use the following OTP to activate your account:</p>
            <h3 style="color:white; background:#16a34a; display:inline-block; padding:10px 20px; border-radius:8px;">
              {otp}
            </h3>
            <p>This OTP is valid for 10 minutes.</p>
          </body>
        </html>
        """

        email_message = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [email])
        email_message.attach_alternative(html_content, "text/html")
        email_message.send()

        request.session['uid'] = user.id
        messages.success(request, "✅ Account created! Check your email for OTP.")
        return redirect('verify_otp')

    return render(request, 'signup.html')


def verify_otp(request):
    if request.method == "POST":
        otp = request.POST['otp']
        uid = request.session.get('uid')

        try:
            user = User.objects.get(id=uid)
            otp_instance = EmailOTP.objects.get(user=user)

            if otp_instance.otp == otp and otp_instance.is_valid():
                user.is_active = True
                user.save()
                otp_instance.delete()
                messages.success(request, "🎉 Email verified successfully! Please login now.")
                return redirect('work_order_analysis')   # ✅ login page pe redirect karega

            else:
                messages.error(request, "❌ Invalid or expired OTP. Try again.")
        except (User.DoesNotExist, EmailOTP.DoesNotExist):
            messages.error(request, "⚠️ Something went wrong, please signup again.")
            return redirect('signup')

    return render(request, 'verify.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('work_order_analysis')  # Redirect to dashboard after login
        else:
            messages.error(request, "Invalid email or password")

    return render(request, 'login.html')

# Logout
def logout_view(request):
    logout(request)
    return redirect('login')

# Forgot Password
def forgot_password(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                profile = user.profile
                otp = profile.generate_otp()
                send_mail(
                    'Password Reset OTP',
                    f'Your OTP for password reset is {otp}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False
                )
                request.session['reset_user'] = user.id
                return redirect('verify_otp')
            except User.DoesNotExist:
                messages.error(request, "No user found with this email.")
    else:
        form = ForgotPasswordForm()
    return render(request, "forgot_password.html", {"form": form})

def work_order_analysis(request):
    all_orders = ManufacturingOrder.objects.all()
    status_counts = {
            'All': all_orders.count(),
            'Draft': all_orders.filter(status='Draft').count(),
            'Confirmed': all_orders.filter(status='Confirmed').count(),
            'In Progress': all_orders.filter(status='In Progress').count(),
            'Completed': all_orders.filter(status='Completed').count(),
            'To Close': all_orders.filter(status='To Close').count(),
            'Not Assigned': all_orders.filter(assignee__isnull=True).count(),
            'Late': all_orders.filter(schedule_date__lt=timezone.now(), status__in=['Draft', 'In Progress']).count(),
        }
    return render(request, 'work_order_analysis.html', {
                'manufacturing_orders': all_orders,
                **status_counts
            })


def new_manufacturing_order(request):
    if request.method == 'POST':
        reference = request.POST.get('reference') or generate_reference()
        schedule_date = request.POST.get('schedule_date')
        product_id = request.POST.get('product')
        assignee_id = request.POST.get('assignee')
        assignee = None
        if assignee_id:
            try:
                assignee = User.objects.get(id=assignee_id)
            except User.DoesNotExist:
                messages.error(request, "Selected assignee does not exist.")
                return redirect('new_manufacturing_order')
        quantity = request.POST.get('quantity')
        unit = request.POST.get('unit')
        bom_id = request.POST.get('bom')
        to_consume_list = request.POST.getlist('to_consume[]')

        # Validate required fields
        errors = []
        if not schedule_date:
            errors.append("Schedule Date is required.")
        if not product_id:
            errors.append("Finished Product is required.")
        if not quantity or float(quantity) <= 0:
            errors.append("Quantity must be a positive number.")
        if not unit or unit not in dict(Product.UNIT_CHOICES).keys():
            errors.append("Unit is required and must be valid.")

        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('new_manufacturing_order')

        try:
            product = get_object_or_404(Product, id=product_id)
            bom = get_object_or_404(BillofMaterials, id=bom_id) if bom_id else None
            assignee = get_object_or_404(User, id=assignee_id) if assignee_id else None
            quantity = float(quantity)

            # Check if reference is unique
            if ManufacturingOrder.objects.filter(reference=reference).exists():
                messages.error(request, "Reference already exists.")
                return redirect('new_manufacturing_order')

            manufacturing_order = ManufacturingOrder.objects.create(
                reference=reference,
                schedule_date=schedule_date,
                product=product,
                assignee=assignee if assignee else None,  # ✅ User object now
                quantity=quantity,
                unit=unit,
                bom=bom,
                status='Draft',
                created_at=timezone.now()
            )
            # Save components (only from BOM if provided)
            if bom:
                components = Component.objects.filter(bill_of_material=bom)
                for i, component in enumerate(components):
                    to_consume = float(to_consume_list[i]) if i < len(to_consume_list) else 0
                    if to_consume > 0:
                        if to_consume > component.available_quantity:
                            messages.error(
                                request,
                                f"Cannot consume {to_consume} of {component.name}; only {component.available_quantity} available."
                            )
                            manufacturing_order.delete()  # rollback
                            return redirect('new_manufacturing_order')
                        ManufacturingOrderComponent.objects.create(
                            manufacturing_order=manufacturing_order,
                            component=component,
                            to_consume=to_consume
                        )

            messages.success(request, f"Manufacturing Order {manufacturing_order.reference} created successfully!")
            return redirect('work_order_analysis')

        except ValueError as e:
            messages.error(request, f"Invalid quantity or component data: {str(e)}")
            return redirect('new_manufacturing_order')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('new_manufacturing_order')

    else:
        products = Product.objects.all()
        users = User.objects.all()
        boms = BillofMaterials.objects.all()
        components = Component.objects.all()

        context = {
            'products': products,
            'users': users,
            'boms': boms,
            'components': components,
            'units': Product.UNIT_CHOICES,
            'mo': {'reference': generate_reference()},  # auto-generated reference
        }
        return render(request, 'new_manu.html', context)
        
def generate_reference():
    today = datetime.date.today().strftime("%Y%m%d")
    count = ManufacturingOrder.objects.filter(reference__startswith=f"MO-{today}").count() + 1
    return f"MO-{today}-{count:04d}"

def get_components(request, bom_id):
    try:
        bom = BillofMaterials.objects.get(id=bom_id)
        components = Component.objects.filter(product=bom.product)  # Adjust filter as needed
        data = [{'name': c.name, 'available_quantity': c.available_quantity, 'unit': c.unit} for c in components]
        return JsonResponse({'components': data})
    except BillofMaterials.DoesNotExist:
        return JsonResponse({'components': []})
    

def manufacturing_products(request):
    products = Product.objects.all()
    return render(request, "manufacturing_products.html", {"products": products})

def work_products(request):
    manufacturing_orders = ManufacturingOrder.objects.all()

    status_counts = {
        'All': ManufacturingOrder.objects.count(),
        'Draft': ManufacturingOrder.objects.filter(status='Draft').count(),
        'Confirmed': ManufacturingOrder.objects.filter(status='Confirmed').count(),
        'In Progress': ManufacturingOrder.objects.filter(status='In Progress').count(),
        'Completed': ManufacturingOrder.objects.filter(status='Completed').count(),
        'To Close': ManufacturingOrder.objects.filter(status='To Close').count(),
        'Not Assigned': ManufacturingOrder.objects.filter(status='Not Assigned').count(),
        'Late': ManufacturingOrder.objects.filter(status='Late').count(),
    }

    return render(request, 'work_products.html', {
        'manufacturing_orders': manufacturing_orders,
        'status_counts': status_counts,
    })

# 2️⃣ View details of a single work order
def view_work_order(request, pk):
    work_order = get_object_or_404(ManufacturingOrder, pk=pk)
    return render(request, 'view_work_order.html', {'work_order': work_order})

def delete_work_order(request, pk):
    order = get_object_or_404(ManufacturingOrder, pk=pk)
    order.delete()
    return redirect('work_products')  # redirect back to the list

def edit_work_order(request, pk):
    work_order = get_object_or_404(ManufacturingOrder, pk=pk)

    if request.method == 'POST':
        form = ManufacturingOrderForm(request.POST, instance=work_order)
        if form.is_valid():
            form.save()
            return redirect('work_products')  # or wherever you want
    else:
        form = ManufacturingOrderForm(instance=work_order)

    return render(request, 'edit_work_order.html', {'form': form, 'work_order': work_order})

def bills_of_materials(request):
    boms = BillofMaterials.objects.prefetch_related("components").all()
    return render(request, "bills_of_materials.html", {"boms": boms})

from .models import WorkCenter

def work_center(request):
    work_centers = WorkCenter.objects.all()
    return render(request, 'work_center.html', {"work_centers": work_centers})

def edit_work_center(request, pk):
    wc = get_object_or_404(WorkCenter, pk=pk)

    if request.method == "POST":
        name = request.POST.get("name")
        cost_per_hour = request.POST.get("cost_per_hour")

        if not name or not cost_per_hour:
            messages.error(request, "All fields are required!")
            return redirect('edit_work_center', pk=pk)

        wc.name = name
        wc.cost_per_hour = cost_per_hour
        wc.save()
        messages.success(request, f"Work Center '{wc.name}' updated successfully!")
        return redirect("work_center")

    return render(request, "edit_work_center.html", {"wc": wc})


def new_work_center(request):
    if request.method == "POST":
        name = request.POST.get("name")
        cost_per_hour = request.POST.get("cost_per_hour")

        if name and cost_per_hour:
            WorkCenter.objects.create(name=name, cost_per_hour=cost_per_hour)
            messages.success(request, f"Work Center '{name}' created successfully!")
            return redirect("work_center")
        else:
            messages.error(request, "All fields are required!")

    return render(request, "new_work_center.html")

def delete_work_center(request, pk):
    wc = get_object_or_404(WorkCenter, pk=pk)
    wc.delete()
    return redirect("work_center")



def new_order(request):
    products = Product.objects.all()
    units = Product.UNIT_CHOICES

    if request.method == "POST":
        bom_name = request.POST.get("bom_name")
        product_id = request.POST.get("product")
        quantity = request.POST.get("quantity")
        unit = request.POST.get("unit")

        component_names = request.POST.getlist("component_name[]")
        component_quantities = request.POST.getlist("component_quantity[]")
        component_units = request.POST.getlist("component_unit[]")

        try:
            product = Product.objects.get(id=product_id)

            # 🔹 Create BOM
            bom = BillofMaterials.objects.create(
                product=product,
                name=bom_name,
                quantity=quantity,
                unit=unit,
            )

            # 🔹 Create Components
            for i in range(len(component_names)):
                name = component_names[i]
                qty = component_quantities[i]
                unit_val = component_units[i]

                if name and qty and unit_val:
                    Component.objects.create(
                        bom=bom,
                        name=name,
                        quantity=qty,
                        unit=unit_val,
                    )

            messages.success(request, f"BOM '{bom.name}' created successfully!")
            return redirect("bills_of_materials")

        except Product.DoesNotExist:
            messages.error(request, "❌ Selected product does not exist.")
            return redirect("new_order")

        except Exception as e:
            messages.error(request, f"⚠️ Error: {str(e)}")
            return redirect("new_order")

    return render(request, "new_order.html", {"products": products, "units": units})


def stock_ledger(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            try:
                product = form.save(commit=False)
                product.save()
                product.recalc_totals()

                # ✅ Optional: Create an initial stock ledger entry if quantity > 0
                if product.on_hand > 0:
                    StockLedgerEntry.objects.create(
                        product=product,
                        movement_type='IN',
                        quantity=product.on_hand,
                        reference="Initial Stock"
                    )

                messages.success(request, "Product saved successfully!")
                return redirect('stock_ledger')
            except Exception as e:
                messages.error(request, f"Error saving product: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ProductForm()

    products = Product.objects.all()
    ledger_entries = StockLedgerEntry.objects.select_related("product")

    context = {
        'products': products,
        'ledger_entries': ledger_entries,
        'form': form,
    }
    return render(request, 'stock_ledger.html', context)

def stock_product_edit(request, product_id):
    product = Product.objects.get(id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            try:
                product = form.save(commit=False)
                product.save()
                product.recalc_totals()
                messages.success(request, "Product updated successfully!")
                return redirect('stock_ledger')
            except Exception as e:
                messages.error(request, f"Error updating product: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ProductForm(instance=product)
    context = {
        'products': Product.objects.all(),
        'form': form,
        'edit_product': product,
    }
    return render(request, 'stock_ledger.html', context)

def stock_product_new(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.total_value = product.unit_cost * product.on_hand
            product.save()
            return redirect("stock_ledger")
    else:
        form = ProductForm()
    return render(request, "stock_product_form.html", {"form": form})