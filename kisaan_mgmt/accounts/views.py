from django.shortcuts import render, redirect
from .models import EmailOTP, Profile
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django import forms
from .forms import SignUpForm
from datetime import timedelta
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import login
from django.urls import reverse
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.views import LoginView
from django.contrib.auth import login, logout
from django.shortcuts import redirect
from django.contrib import messages

def send_otp(email, otp):
    subject = "Your OTP for Kisaan App Registration"
    message = f"Your OTP is {otp}. It is valid for 3 minutes."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            signup_data = form.cleaned_data.copy()
            signup_data.pop('password2', None)
            request.session['signup_data'] = signup_data

            email = signup_data['email']
            otp_obj, created = EmailOTP.objects.get_or_create(email=email)
            otp_obj.generate_otp()
            send_otp(email, otp_obj.otp)

            print(f"OTP sent to {email}: {otp_obj.otp}")
            return redirect('verify-otp')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})

def verify_otp_view(request):
    signup_data = request.session.get('signup_data')
    if not signup_data:
        return redirect('signup')

    email = signup_data.get('email')
    try:
        otp_obj = EmailOTP.objects.get(email=email)
    except EmailOTP.DoesNotExist:
        return redirect('signup')

    now = timezone.now()
    expiry_time = otp_obj.created_at + timedelta(minutes=3)
    seconds_left = max(0, (expiry_time - now).total_seconds())
    can_resend = seconds_left == 0

    if request.method == 'POST' and 'resend_otp' in request.POST:
        if not can_resend:
            messages.warning(request, f"Please wait {int(seconds_left)} seconds before resending OTP.")
        else:
            otp_obj.generate_otp()
            otp_obj.save()
            send_otp(email, otp_obj.otp)
            messages.success(request, "A new OTP has been sent to your email.")
            seconds_left = 180
            can_resend = False
        return render(request, 'accounts/verify_otp.html', {
            'email': email,
            'seconds_left': int(seconds_left),
            'can_resend': can_resend,
        })

    if request.method == 'POST' and 'otp' in request.POST:
        entered_otp = request.POST.get('otp', '').strip()

        if otp_obj.is_valid() and otp_obj.otp == entered_otp:
            if User.objects.filter(email=email).exists():
                del request.session['signup_data']
                EmailOTP.objects.filter(email=email).delete()
                messages.success(request, "You are already registered! Please log in.")
                return redirect('login')

            # ✅ Create user (Profile will be auto-created by signal)
            user = User.objects.create_user(
                username=signup_data['username'],
                email=email,
                password=signup_data['password1']
            )

            # ✅ Update profile
            profile = user.profile
            profile.phonenumber = signup_data.get('phonenumber', '')
            profile.ward = signup_data.get('ward', '')
            profile.tole = signup_data.get('tole', '')
            profile.role = signup_data.get('role', '')
            profile.save()

            del request.session['signup_data']
            EmailOTP.objects.filter(email=email).delete()
            messages.success(request, "Registered successfully!")

            # ✅ Redirect based on role
            if profile.role == 'farmer':
                return redirect('farmer-login')
            elif profile.role == 'customer':
                return redirect('customer-login')
            else:
                return redirect('login')
        else:
            return render(request, 'accounts/verify_otp.html', {
                'email': email,
                'error': 'Invalid or expired OTP. Please try again.',
                'seconds_left': int(seconds_left),
                'can_resend': can_resend,
            })

    return render(request, 'accounts/verify_otp.html', {
        'email': email,
        'seconds_left': int(seconds_left),
        'can_resend': can_resend,
    })


# =======================
# DASHBOARDS
# =======================

@login_required
def farmer_dashboard_view(request):
    return render(request, 'accounts/farmer_dashboard.html')

@login_required
def customer_dashboard_view(request):
    return render(request, 'accounts/customer_dashboard.html')

# =======================
# ROLE-BASED REDIRECT
# =======================

@login_required
def role_based_redirect(request):
    try:
        profile = request.user.profile
    except Exception:
        # Profile doesn't exist for some reason
        return redirect('login')

    if profile.role == 'farmer':
        return redirect('farmer-dashboard')
    elif profile.role == 'customer':
        return redirect('customer-dashboard')
    else:
        # fallback for unexpected role or missing role
        return redirect('login')

class FarmerLoginView(LoginView):
    template_name = 'accounts/farmer_login.html'
    redirect_authenticated_user = False

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.profile.role == 'farmer':
                return redirect('farmer-dashboard')
            else:
                logout(request)  # logout wrong role
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        if user.profile.role == 'farmer':
            login(self.request, user)
            return redirect('farmer-dashboard')
        else:
            messages.error(self.request, "Access denied. Not a farmer.")
            return redirect('farmer-login')

class CustomerLoginView(LoginView):
    template_name = 'accounts/customer_login.html'
    redirect_authenticated_user = False

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if request.user.profile.role == 'customer':
                return redirect('customer-dashboard')
            else:
                logout(request)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        if user.profile.role == 'customer':
            login(self.request, user)
            return redirect('customer-dashboard')
        else:
            messages.error(self.request, "Access denied. Not a customer.")
            return redirect('customer-login')
