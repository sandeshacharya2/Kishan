from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from datetime import timedelta
from django.utils.translation import gettext as _

from ..models import EmailOTP, Profile, FarmerProfile
from ..forms import SignUpForm, FarmerProfileForm
from products.models import Product


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

        messages.success(request, _('तपाईंको सन्देश सफलतापूर्वक पठाइयो।'))

    return render(request, 'landingpage/contact.html')


def switch_to_farmer(request):
    logout(request)
    return redirect('farmer-login')

def switch_to_customer(request):
    logout(request)
    return redirect('customer-login')


# ✅ Send OTP Email
def send_otp(email, otp):
    subject = _("किसान app को लागि तपाइको OTP")
    message = _(f"तपाइको OTP {otp}. यो OTP ३ मिनेट सम्म मात्र मान्य हुनेछ ।")
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])


# ✅ SignUp View (cleaned, kept full version)
def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            allowed_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com', 'mail.com', 'zoho.com']
            domain = email.split('@')[-1].lower()

            if domain not in allowed_domains:
                messages.error(request, _("यो ईमेल डोमेन अनुमति छैन। कृपया अरु डोमेन प्रयोग गर्नुहोस्।"))
                return render(request, 'accounts/signup.html', {'form': form})

            signup_data = form.cleaned_data.copy()      #retrieve form data in dictionary
            signup_data.pop('password2', None)

            signup_data['latitude'] = request.POST.get('latitude')      #the first part is the key, the second part is the value in dictionary signup_data
            signup_data['longitude'] = request.POST.get('longitude')    

            request.session['signup_data'] = signup_data

            """signup_data = form.cleaned_data.copy()	Get form data temporarily (this view only)
                request.session['signup_data'] = signup_data	Store data across views (OTP, login, etc.)"""
            # Cleanup expired OTPs
            EmailOTP.cleanup_expired()      #calls the cleanup_expired method from model to delete expired OTPs

            # Delete any existing OTP for this email before creating a new one
            EmailOTP.objects.filter(email=email).delete()

            otp_obj = EmailOTP.objects.create(email=email)      #creates a new OTP object with the email
            otp_obj.generate_otp()     #generate a new OTP through the generate_otp method in model
            send_otp(email, otp_obj.otp)        #sending the otp through send_otp function

            print(f"OTP sent to {email}: {otp_obj.otp}")
            return redirect('verify-otp')
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {'form': form})


# ✅ OTP Verification View
def verify_otp_view(request):
    EmailOTP.cleanup_expired()  #delete expired OTPs before processing

    signup_data = request.session.get('signup_data') #retrieves the signup data from session
    if not signup_data:
        return redirect('signup')

    email = signup_data.get('email') #gets the email from signup data
    try:
        otp_obj = EmailOTP.objects.get(email=email)
    except EmailOTP.DoesNotExist:
        return redirect('signup')

    now = timezone.now()        #This gets the current date and time
    expiry_time = otp_obj.created_at + timedelta(minutes=3) # This calculates the expiry time of the OTP
    seconds_left = max(0, (expiry_time - now).total_seconds())
    can_resend = seconds_left == 0

    # Resend OTP
    if request.method == 'POST' and 'resend_otp' in request.POST:   #post method and user clicks resend OTP button
        if not can_resend:
            messages.warning(request, f"पर्खनुहोस्, OTP पुन: पठाउन {int(seconds_left)} सेकेन्ड बाकी छ।")
        else:
            otp_obj.generate_otp()
            otp_obj.save()
            send_otp(email, otp_obj.otp)
            messages.success(request, "तपाइँको इमेलमा नयाँ OTP पठाइएको छ।")
            seconds_left = 180
            can_resend = False

        return render(request, 'accounts/verify_otp.html', {
            'email': email,
            'seconds_left': int(seconds_left),
            'can_resend': can_resend,
        })

    # Submit OTP
    if request.method == 'POST' and 'otp' in request.POST:
        entered_otp = request.POST.get('otp', '').strip()       #Gets the OTP the user entered from the form data.

        if otp_obj.is_valid() and otp_obj.otp == entered_otp:
            if User.objects.filter(email=email).exists():
                del request.session['signup_data']
                EmailOTP.objects.filter(email=email).delete()
                messages.success(request, "तपाईं पहिले नै दर्ता भइसकेको हुनाले लगइन पृष्ठमा जानुहोस्।")
                return redirect('login')

            user = User.objects.create_user(
                username=signup_data['username'],
                email=email,
                password=signup_data['password1']
            )

            profile = user.profile
            profile.phonenumber = signup_data.get('phonenumber')
            profile.ward = signup_data.get('ward')
            profile.tole = signup_data.get('tole')
            profile.role = signup_data.get('role')
            profile.latitude = float(signup_data.get('latitude') or 0)
            profile.longitude = float(signup_data.get('longitude') or 0)
            profile.save()

            del request.session['signup_data']
            EmailOTP.objects.filter(email=email).delete()
            messages.success(request, "दर्ता सफल भयो!")

            if profile.role == 'farmer':
                return redirect('farmer-login')
            elif profile.role == 'customer':
                return redirect('customer-login')
            return redirect('login')
        else:
            return render(request, 'accounts/verify_otp.html', {
                'email': email,
                'error': 'OTP गलत वा म्याद सकिएको छ। कृपया पुन: प्रयास गर्नुहोस्।',
                'seconds_left': int(seconds_left),
                'can_resend': can_resend,
            })

    return render(request, 'accounts/verify_otp.html', {
        'email': email,
        'seconds_left': int(seconds_left),
        'can_resend': can_resend,
    })


# ✅ Dashboards
@login_required
def farmer_dashboard_view(request):
    user = request.user
    products = Product.objects.filter(farmer=user)

    try:
        farmer_profile = user.farmerprofile
    except FarmerProfile.DoesNotExist:
        farmer_profile = None

    try:
        accounts_profile = user.profile
    except Profile.DoesNotExist:
        accounts_profile = None

    form = FarmerProfileForm(instance=farmer_profile)

    context = {
        'products': products,
        'form': form,
        'farmerprofile': farmer_profile,
        'accounts_profile': accounts_profile,
    }
    return render(request, 'accounts/farmer_dashboard.html', context)


# @login_required
# def customer_dashboard_view(request):
#     products = Product.objects.all().order_by('-date_posted')

#     try:
#         customer_profile = request.user.customerprofile
#     except:
#         customer_profile = None

#     return render(request, 'accounts/customer_dashboard.html', {
#         'products': products,
#         'customer_profile': customer_profile,
#     })
