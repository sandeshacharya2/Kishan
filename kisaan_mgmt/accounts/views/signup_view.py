from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from datetime import timedelta
from django.utils.translation import gettext as _
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_GET
from django.db.models import Avg

# Models
from accounts.models import (
    EmailOTP, Profile, FarmerProfile, CustomerProfile, FarmerReview
)

# Forms
from accounts.forms import SignUpForm, FarmerProfileForm, FarmerReviewForm

# Other apps
from products.models import Product
from chat.models import ChatRoom

# Decorators (defined in this file or imported correctly)
# Assuming `farmer_required` and `customer_required` are defined below or in same file
# If they are in this file, no import needed. If not, adjust accordingly.

# Remove this incorrect import:
# from accounts.views.role_based_redirect import farmer_required, customer_required


# ======================
# DECORATORS (if not already defined above)
# ======================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from datetime import timedelta
from django.utils.translation import gettext as _
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_GET
from django.db.models import Avg

# Models
from accounts.models import (
    EmailOTP, Profile, FarmerProfile, CustomerProfile, FarmerReview
)

# Forms
from accounts.forms import SignUpForm, FarmerProfileForm, FarmerReviewForm
# ⚠️ Make sure you also have CustomerProfileForm — if not, create one or use FarmerProfileForm as base
# from accounts.forms import CustomerProfileForm  # ← Uncomment when available

# Other apps
from products.models import Product
from chat.models import ChatRoom


# ======================
# DECORATORS
# ======================

def farmer_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.role == 'farmer':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, _("Only farmers can access this page."))
            return redirect('farmer-login')
    return wrapper


def customer_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if hasattr(request.user, 'profile') and request.user.profile.role == 'customer':
            return view_func(request, *args, **kwargs)
        else:
            messages.error(request, _("Only customers can access this page."))
            return redirect('customer-login')
    return wrapper


# ======================
# PUBLIC VIEWS
# ======================

def landing_page(request):
    return render(request, 'landingpage/index.html')


def about(request):
    return render(request, 'landingpage/about.html')


def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        full_message = f"नाम: {name}\nइमेल: {email}\n\nसन्देश:\n{message}"

        send_mail(
            subject=subject,
            message=full_message,
            from_email='kisaan.helps@gmail.com',
            recipient_list=['kisaan.helps@gmail.com'],
            fail_silently=False,
        )

        messages.success(request, _('Your message has been sent successfully!'))

    return render(request, 'landingpage/contact.html')


@require_GET
def check_availability(request):
    field = request.GET.get('field')
    value = request.GET.get('value', '').strip()

    if not field or not value:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    if field == 'username':
        exists = User.objects.filter(username=value).exists()
    elif field == 'email':
        exists = User.objects.filter(email=value).exists()
    elif field == 'phonenumber':
        exists = FarmerProfile.objects.filter(phonenumber=value).exists() or \
                 CustomerProfile.objects.filter(phonenumber=value).exists()
    else:
        return JsonResponse({'error': 'Invalid field'}, status=400)

    return JsonResponse({'exists': exists})


# ======================
# AUTH & PROFILE VIEWS
# ======================

def switch_to_farmer(request):
    logout(request)
    return redirect('farmer-login')


def switch_to_customer(request):
    logout(request)
    return redirect('customer-login')


def send_otp(email, otp):
    subject = _("Your OTP for Kisaan app")
    message = _(f"Your OTP is {otp}. This OTP is valid for 3 minutes. If you did not request this, please ignore this email.")
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            allowed_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com', 'mail.com', 'zoho.com']
            domain = email.split('@')[-1].lower()

            if domain not in allowed_domains:
                messages.error(request, _("This email domain is not allowed. Please use a common email provider."))
                return render(request, 'accounts/signup.html', {'form': form})

            signup_data = form.cleaned_data.copy()
            signup_data.pop('password2', None)
            signup_data['latitude'] = request.POST.get('latitude')
            signup_data['longitude'] = request.POST.get('longitude')
            request.session['signup_data'] = signup_data

            EmailOTP.cleanup_expired()
            EmailOTP.objects.filter(email=email).delete()

            otp_obj = EmailOTP.objects.create(email=email)
            otp_obj.generate_otp()
            send_otp(email, otp_obj.otp)

            return redirect('verify-otp')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})


def verify_otp_view(request):
    EmailOTP.cleanup_expired()
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
            messages.warning(request, f"Wait {int(seconds_left)} seconds before resending.")
        else:
            otp_obj.generate_otp()
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
                messages.success(request, "You are already registered. Please log in.")
                return redirect('login')

            user = User.objects.create_user(
                first_name=signup_data.get('first_name', ''),
                last_name=signup_data.get('last_name', ''),
                username=signup_data['username'],
                email=email,
                password=signup_data['password1']
            )

            profile = user.profile
            profile.role = signup_data.get('role')
            profile.save()

            role = signup_data.get('role')
            if role == 'farmer':
                farmer_profile, _ = FarmerProfile.objects.get_or_create(user=user)
                farmer_profile.phonenumber = signup_data.get('phonenumber')
                farmer_profile.ward = signup_data.get('ward')
                farmer_profile.tole = signup_data.get('tole')
                farmer_profile.latitude = float(signup_data.get('latitude') or 0)
                farmer_profile.longitude = float(signup_data.get('longitude') or 0)
                farmer_profile.save()
            elif role == 'customer':
                customer_profile, _ = CustomerProfile.objects.get_or_create(user=user)
                customer_profile.phonenumber = signup_data.get('phonenumber')
                customer_profile.ward = signup_data.get('ward')
                customer_profile.tole = signup_data.get('tole')
                customer_profile.latitude = float(signup_data.get('latitude') or 0)
                customer_profile.longitude = float(signup_data.get('longitude') or 0)
                customer_profile.save()

            del request.session['signup_data']
            EmailOTP.objects.filter(email=email).delete()
            messages.success(request, "Registration successful. You can now log in.")

            if role == 'farmer':
                return redirect('farmer-login')
            else:
                return redirect('customer-login')
        else:
            return render(request, 'accounts/verify_otp.html', {
                'email': email,
                'error': 'Invalid or expired OTP.',
                'seconds_left': int(seconds_left),
                'can_resend': can_resend,
            })

    return render(request, 'accounts/verify_otp.html', {
        'email': email,
        'seconds_left': int(seconds_left),
        'can_resend': can_resend,
    })


@login_required
def role_based_redirect(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, _("Profile not found. Please log in again."))
        return redirect('login')

    if profile.role == 'farmer':
        farmer_profile, created = FarmerProfile.objects.get_or_create(user=request.user)
        if not farmer_profile.profile_picture:
            return redirect('update-farmer-profile')
        return redirect('farmer-dashboard')

    elif profile.role == 'customer':
        customer_profile, created = CustomerProfile.objects.get_or_create(user=request.user)
        if not customer_profile.profile_picture:
            return redirect('update-customer-profile')
        return redirect('customer-dashboard')

    else:
        messages.error(request, _("Illegal access."))
        logout(request)
        return redirect('login')


# ======================
# DASHBOARD VIEWS
# ======================

@login_required
@farmer_required
def farmer_dashboard_view(request):
    farmer_profile = request.user.farmerprofile
    products = Product.objects.filter(farmer=farmer_profile)

    pending_chats = ChatRoom.objects.filter(
        farmer=farmer_profile,
        farmer_accepted=False,
        farmer_rejected=False
    )

    avg_rating = FarmerReview.objects.filter(farmer=farmer_profile).aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating = round(avg_rating, 1)

    reviews = FarmerReview.objects.filter(farmer=farmer_profile).select_related('customer').order_by('-created_at')

    form = FarmerProfileForm(instance=farmer_profile)

    context = {
        'products': products,
        'form': form,
        'farmerprofile': farmer_profile,
        'pending_chats': pending_chats,
        'avg_rating': avg_rating,
        'reviews': reviews,
    }
    return render(request, 'accounts/farmer_dashboard.html', context)


# ======================
# PROFILE UPDATE VIEWS
# ======================

@login_required
@farmer_required
def update_farmer_profile(request):
    farmer_profile = request.user.farmerprofile
    if request.method == 'POST':
        form = FarmerProfileForm(request.POST, request.FILES, instance=farmer_profile)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated successfully!"))
            return redirect('farmer-dashboard')
    else:
        form = FarmerProfileForm(instance=farmer_profile)
    return render(request, 'accounts/update_farmer_profile.html', {'form': form})


@login_required
@customer_required
def update_customer_profile(request):
    customer_profile, created = CustomerProfile.objects.get_or_create(user=request.user)
    # ⚠️ Replace `FarmerProfileForm` with `CustomerProfileForm` if you create one
    # For now, assuming same fields — adjust as needed
    if request.method == 'POST':
        form = FarmerProfileForm(request.POST, request.FILES, instance=customer_profile)
        if form.is_valid():
            form.save()
            messages.success(request, _("Profile updated successfully!"))
            return redirect('customer-dashboard')
    else:
        form = FarmerProfileForm(instance=customer_profile)
    return render(request, 'accounts/update_customer_profile.html', {'form': form})


# ======================
# FARMER REVIEW VIEWS
# ======================

@login_required
@customer_required
def submit_farmer_review(request, farmer_id):
    farmer_profile = get_object_or_404(FarmerProfile, id=farmer_id)
    customer_profile = request.user.customerprofile

    review, created = FarmerReview.objects.get_or_create(
        farmer=farmer_profile,
        customer=customer_profile,
        defaults={'rating': 5}
    )

    if request.method == 'POST':
        form = FarmerReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, _("Your review has been submitted!"))
            return redirect('farmer_detail', farmer_id=farmer_id)
    else:
        form = FarmerReviewForm(instance=review)

    return render(request, 'accounts/submit_farmer_review.html', {
        'form': form,
        'farmer': farmer_profile,
    })


@login_required
@farmer_required
def farmer_reviews_view(request):
    farmer_profile = request.user.farmerprofile
    reviews = FarmerReview.objects.filter(farmer=farmer_profile).select_related('customer').order_by('-created_at')
    return render(request, 'accounts/farmer_reviews.html', {
        'reviews': reviews,
        'farmer': farmer_profile,
    })


@login_required
def customer_farmer_reviews_view(request, farmer_id):
    """Anyone logged in can view reviews of a specific farmer"""
    farmer_profile = get_object_or_404(FarmerProfile, id=farmer_id)
    reviews = FarmerReview.objects.filter(farmer=farmer_profile).select_related('customer').order_by('-created_at')
    avg_rating = FarmerReview.objects.filter(farmer=farmer_profile).aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating = round(avg_rating, 1)
    return render(request, 'accounts/farmer_reviews_customer.html', {
        'reviews': reviews,
        'farmer': farmer_profile,
        'avg_rating': avg_rating,
    })


@login_required
@farmer_required
def customer_detail_view(request, customer_id):
    farmer_profile = request.user.farmerprofile
    customer_profile = get_object_or_404(CustomerProfile, id=customer_id)

    review = FarmerReview.objects.filter(
        farmer=farmer_profile,
        customer=customer_profile
    ).first()

    return render(request, 'accounts/customer_detail.html', {
        'customer': customer_profile,
        'review': review,
    })


# ======================
# OTHER VIEWS
# ======================

def view_farmer_location(request, farmer_id):
    farmer = get_object_or_404(FarmerProfile, id=farmer_id)
    return render(request, 'accounts/farmer_location.html', {'farmer': farmer})


def farmer_detail(request, farmer_id):
    farmer = get_object_or_404(FarmerProfile, id=farmer_id)
    avg_rating = FarmerReview.objects.filter(farmer=farmer).aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating = round(avg_rating, 1)
    return render(request, 'accounts/farmer_detail.html', {
        'farmer': farmer,
        'avg_rating': avg_rating,
    })