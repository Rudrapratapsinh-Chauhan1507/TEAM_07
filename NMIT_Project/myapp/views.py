from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import SignupForm, LoginForm, ForgotPasswordForm, OTPVerificationForm
from django.core.mail import send_mail
from django.conf import settings
from .models import EmailOTP
from django.core.mail import EmailMultiAlternatives
from .models import Product, BillOfMaterial, Component
from .models import ManufacturingOrder
from .forms import ProductForm


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
                messages.success(request, "🎉 Email verified successfully! You can now login.")
                return redirect('login')
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
    statuses = ['Draft', 'Confirmed', 'In-Progress', 'To Close', 'Not Assigned', 'Late']

    # Get all manufacturing orders
    manufacturing_orders = ManufacturingOrder.objects.all()

    # Group orders by status
    orders_by_status = [(status, manufacturing_orders.filter(status=status)) for status in statuses]

    context = {
        'manufacturing_orders': manufacturing_orders,
        'orders_by_status': orders_by_status,
    }

    return render(request, 'work_order_analysis.html', context)

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ManufacturingOrder, ManufacturingOrderComponent, Product, BillOfMaterial, Component, User
from django.utils import timezone

def new_manufacturing_order(request):
    if request.method == 'POST':
        # Extract form data
        reference = request.POST.get('reference')
        schedule_date = request.POST.get('schedule_date')
        product_id = request.POST.get('product')
        assignee = request.POST.get('assignee')
        quantity = request.POST.get('quantity')
        unit = request.POST.get('unit')
        bom_id = request.POST.get('bom')
        to_consume_list = request.POST.getlist('to_consume[]')  # List of component quantities
        status = request.POST.get('status', 'Draft')

        # Validate required fields
        if not all([reference, schedule_date, product_id, quantity, unit]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('new_manufacturing_order')

        try:
            # Get related objects
            product = Product.objects.get(id=product_id)
            bom = BillOfMaterial.objects.get(id=bom_id) if bom_id else None

            # Create ManufacturingOrder instance
            manufacturing_order = ManufacturingOrder.objects.create(
                reference=reference,
                schedule_date=schedule_date,
                product=product,
                assignee=assignee if assignee else None,
                quantity=float(quantity),
                unit=unit,
                bom=bom,
                status=status,
                created_at=timezone.now()
            )

            # Save components (assuming components are passed in the same order as displayed)
            components = Component.objects.all()  # Adjust based on how components are filtered
            for i, to_consume in enumerate(to_consume_list):
                if i < len(components) and float(to_consume) > 0:
                    ManufacturingOrderComponent.objects.create(
                        manufacturing_order=manufacturing_order,
                        component=components[i],
                        to_consume=float(to_consume)
                    )

            messages.success(request, "Manufacturing Order created successfully!")
            return redirect('manufacturing_dashboard')  # Redirect to dashboard or another page

        except Product.DoesNotExist:
            messages.error(request, "Selected product does not exist.")
            return redirect('new_manufacturing_order')
        except BillOfMaterial.DoesNotExist:
            messages.error(request, "Selected Bill of Material does not exist.")
            return redirect('new_manufacturing_order')
        except ValueError:
            messages.error(request, "Invalid quantity or component data.")
            return redirect('new_manufacturing_order')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('new_manufacturing_order')

    else:
        # GET request: Render the form with initial data
        products = Product.objects.all()
        users = User.objects.all()
        boms = BillOfMaterial.objects.all()
        components = Component.objects.all()

        context = {
            'products': products,
            'users': users,
            'boms': boms,
            'components': components,
            'mo': {'reference': ''},  # Placeholder for default values if needed
        }
        return render(request, 'new_manu.html', context)

def manufacturing_products(request):
    products = Product.objects.all()
    return render(request, "manufacturing_products.html", {"products": products})

def work_products(request):
    products = []
    return render(request, "work_products.html", {"products": products})

def bills_of_materials(request):
    boms = BillOfMaterial.objects.all()
    return render(request, "bills_of_materials.html", {"boms": boms})

def work_center(request):
    return render(request, 'work_center.html')


def new_order(request):
    if request.method == "POST":
        print("✅ Form submitted!", request.POST)  # debug log

        # process + save data as before...
        return redirect("work_order_analysis")

    return render(request, "new_order.html")

def stock_ledger(request):
    products = Product.objects.all()
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.recalc_totals()
            product.save()
            messages.success(request, "✅ Product saved successfully!")
            return redirect("stock_ledger")
    else:
        form = ProductForm()
    return render(request, "stock_ledger.html", {"products": products, "form": form})

def stock_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            product.recalc_totals()
            product.save()
            messages.success(request, "✅ Product updated successfully!")
            return redirect("stock_ledger")
    else:
        form = ProductForm(instance=product)
    return render(request, "stock_ledger.html", {"products": Product.objects.all(), "form": form, "edit_product": product})

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