from django import forms
from django.contrib.auth.models import User
from .models import ManufacturingOrder, Product, BillOfMaterial, WorkCenter,Profile

class SignupForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    full_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))

class OTPVerificationForm(forms.Form):
    otp = forms.CharField(max_length=6, widget=forms.TextInput(attrs={'class': 'form-control'}))

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'unit_cost', 'unit', 'on_hand', 'free_to_use', 'incoming', 'outgoing']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'on_hand': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'free_to_use': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'incoming': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'outgoing': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class ManufacturingOrderForm(forms.ModelForm):
    class Meta:
        model = ManufacturingOrder
        fields = ['reference', 'schedule_date', 'product', 'quantity', 'unit', 'bom', 'assignee', 'status']
        widgets = {
            'reference': forms.TextInput(attrs={'class': 'w-full rounded-lg px-4 py-2 bg-gray-900 text-gray-200 border border-gray-700'}),
            'schedule_date': forms.DateInput(attrs={'type': 'date', 'class': 'w-full rounded-lg px-4 py-2 bg-gray-900 text-gray-200 border border-gray-700'}),
            'quantity': forms.NumberInput(attrs={'class': 'flex-1 rounded-lg px-4 py-2 bg-gray-900 text-gray-200 border border-gray-700'}),
            'unit': forms.Select(attrs={'class': 'w-28 rounded-lg px-4 py-2 bg-gray-900 text-gray-200 border border-gray-700'}),
            'status': forms.HiddenInput(),
            'product': forms.Select(attrs={'class': 'w-full rounded-lg px-4 py-2 bg-gray-900 text-gray-200 border border-gray-700'}),
            'bom': forms.Select(attrs={'class': 'w-full rounded-lg px-4 py-2 bg-gray-900 text-gray-200 border border-gray-700'}),
            'assignee': forms.Select(attrs={'class': 'w-full rounded-lg px-4 py-2 bg-gray-900 text-gray-200 border border-gray-700'}),
        }

class WorkCenterForm(forms.ModelForm):
    class Meta:
        model = WorkCenter
        fields = ['name', 'cost_per_hour']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'cost_per_hour': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }