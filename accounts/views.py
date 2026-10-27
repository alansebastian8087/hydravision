from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db import transaction
from django import forms
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.validators import validate_email
import re

from customers.models import Customer
from .models import Profile


class ClientRegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        error_messages={
            'required': 'Username is required.',
        }
    )

    email = forms.EmailField(
        error_messages={
            'required': 'Email is required.',
            'invalid': 'Enter a valid email address.',
        }
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        error_messages={
            'required': 'Password is required.',
        }
    )

    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        error_messages={
            'required': 'Please confirm your password.',
        }
    )

    name = forms.CharField(
        max_length=20,
        error_messages={
            'required': 'Name is required.',
        }
    )

    phone = forms.CharField(
        max_length=10,
        required=False
    )

    address = forms.CharField(
        widget=forms.Textarea,
        required=False
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()

        if len(username) < 4:
            raise forms.ValidationError("Username must be at least 4 characters long.")

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists.")

        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()

        validate_email(email)

        if not re.fullmatch(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
            raise forms.ValidationError("Enter a valid email address.")

        domain_part = email.split('@')[-1]
        if '.' not in domain_part:
            raise forms.ValidationError("Email domain must contain a dot (example: gmail.com).")

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists.")

        return email

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()

        if not name:
            raise forms.ValidationError("Name is required.")

        if len(name) > 20:
            raise forms.ValidationError("Name must be 20 characters or less.")

        if not re.fullmatch(r"[A-Za-z ]+", name):
            raise forms.ValidationError("Name should contain only letters and spaces.")

        return name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()

        if phone:
            phone = re.sub(r'\D', '', phone)

            if not re.fullmatch(r'^[0-9]{10}$', phone):
                raise forms.ValidationError("Phone number must be exactly 10 digits.")

        return phone

    def clean_password(self):
        password = self.cleaned_data.get('password', '')

        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")

        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError("Password must contain at least one uppercase letter.")

        if not re.search(r'[a-z]', password):
            raise forms.ValidationError("Password must contain at least one lowercase letter.")

        if not re.search(r'\d', password):
            raise forms.ValidationError("Password must contain at least one number.")

        if not re.search(r'[#?!@$%^&*\-]', password):
            raise forms.ValidationError("Password must contain at least one special character.")

        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        return cleaned_data


def register_client(request):
    if request.method == 'POST':
        form = ClientRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'],
                        password=form.cleaned_data['password']
                    )

                    Profile.objects.update_or_create(
                        user=user,
                        defaults={'role': 'Client'}
                    )

                    Customer.objects.update_or_create(
                        email=form.cleaned_data['email'],
                        defaults={
                            'name': form.cleaned_data['name'],
                            'phone': form.cleaned_data['phone'],
                            'address': form.cleaned_data['address'],
                        }
                    )

                messages.success(request, 'Registration successful. Please log in as Client.')
                return redirect('client_login')

            except Exception:
                messages.error(request, 'Registration failed. Please try again.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ClientRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def _get_next_url(request):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return None


def _role_login(request, expected_role, template_name):
    next_url = _get_next_url(request)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                role = user.profile.role
            except Profile.DoesNotExist:
                role = None

            if role == expected_role:
                login(request, user)

                if next_url:
                    return redirect(next_url)

                return redirect('home')
            else:
                messages.error(request, f'This account is not registered as {expected_role}.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, template_name, {'next': next_url})


def client_login(request):
    return _role_login(request, 'Client', 'accounts/client_login.html')


def technician_login(request):
    return _role_login(request, 'Lab Technician', 'accounts/technician_login.html')


def admin_login(request):
    return _role_login(request, 'Admin', 'accounts/admin_login.html')


def user_logout(request):
    logout(request)
    return redirect('home')


def role_redirect(request):
    if not request.user.is_authenticated:
        return redirect('home')

    try:
        role = request.user.profile.role
    except Profile.DoesNotExist:
        return redirect('home')

    if role == 'Admin':
        return redirect('dashboard_home')
    elif role == 'Lab Technician':
        return redirect('technician_dashboard')
    elif role == 'Client':
        return redirect('client_dashboard')

    return redirect('home')


def common_home(request):
    role = None
    if request.user.is_authenticated:
        try:
            role = request.user.profile.role
        except Profile.DoesNotExist:
            role = None

    return render(request, 'accounts/common_home.html', {'role': role})