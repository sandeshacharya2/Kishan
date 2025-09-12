from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.utils.translation import gettext_lazy as _

# Relative imports (since this file is in accounts/views/)
from ..models import CustomerProfile, FarmerProfile, Profile
from ..forms import FarmerProfileForm, CustomerProfileForm


@login_required
def role_based_redirect(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        messages.error(request, _("Profile not found. Please log in again."))
        return redirect('login')

    if profile.role == 'farmer':
        try:
            farmer_profile = request.user.farmerprofile
        except FarmerProfile.DoesNotExist:
            farmer_profile = FarmerProfile.objects.create(user=request.user)

        # Redirect to profile update if required fields are missing
        if not farmer_profile.profile_picture:
            return redirect('update-farmer-profile')

        return redirect('farmer-dashboard')

    elif profile.role == 'customer':
        try:
            customer_profile = request.user.customerprofile
        except CustomerProfile.DoesNotExist:
            customer_profile = CustomerProfile.objects.create(user=request.user)

        # Redirect to profile update if required fields are missing
        if not customer_profile.profile_picture:
            return redirect('update-customer-profile')

        return redirect('customer-dashboard')

    else:
        messages.error(request, _("अवैध भूमिका।"))
        logout(request)
        return redirect('login')


class FarmerLoginView(LoginView):
    template_name = 'accounts/farmer_login.html'
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if hasattr(request.user, 'profile') and request.user.profile.role == 'farmer':
                return redirect('role-redirect')
            else:
                logout(request)
                messages.error(request, _("You must be logged in as a farmer to access this page."))
                return redirect('farmer-login')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        if hasattr(user, 'profile') and user.profile.role == 'farmer':
            login(self.request, user)
            return redirect('role-redirect')
        else:
            logout(self.request)
            messages.error(self.request, _("You are not a farmer. Please use the correct login page."))
            return redirect('farmer-login')


class CustomerLoginView(LoginView):
    template_name = 'accounts/customer_login.html'
    redirect_authenticated_user = True

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if hasattr(request.user, 'profile') and request.user.profile.role == 'customer':
                return redirect('role-redirect')
            else:
                logout(request)
                messages.error(request, _("You must be logged in as a customer to access this page."))
                return redirect('customer-login')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        if hasattr(user, 'profile') and user.profile.role == 'customer':
            login(self.request, user)
            return redirect('role-redirect')
        else:
            logout(self.request)
            messages.error(self.request, _("You are not a customer. Please use the correct login page."))
            return redirect('customer-login')


# ------------------- Decorators -------------------

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


# ------------------- Customer Views (Optional - Uncomment if needed) -------------------

# @customer_required
# def customer_dashboard(request):
#     # Add any customer-specific data to context here if needed
#     return render(request, 'customer/dashboard.html')


# @customer_required
# def update_customer_profile(request):
#     try:
#         customer_profile = request.user.customerprofile
#     except CustomerProfile.DoesNotExist:
#         customer_profile = CustomerProfile.objects.create(user=request.user)

#     if request.method == 'POST':
#         form = CustomerProfileForm(request.POST, request.FILES, instance=customer_profile)
#         if form.is_valid():
#             form.save()
#             messages.success(request, _("प्रोफाइल सफलतापूर्वक अपडेट भयो।"))
#             return redirect('customer-dashboard')
#     else:
#         form = CustomerProfileForm(instance=customer_profile)

#     context = {'form': form, 'profile': customer_profile}
#     return render(request, 'customer/update_profile.html', context)