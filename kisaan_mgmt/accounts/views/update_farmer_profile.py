from django.shortcuts import redirect, render
from ..forms import FarmerProfileForm
from ..models import Profile, FarmerProfile
from django.contrib.auth.decorators import login_required
from ..forms import CustomerProfileForm
from ..models import CustomerProfile
from django.utils.translation import gettext_lazy as _
from accounts.views.role_based_redirect import farmer_required, customer_required

@farmer_required
@login_required
def update_farmer_profile(request):
    user = request.user
    
    # Ensure the user is a farmer
    try:
        profile = user.profile
        if profile.role != 'farmer':
            return redirect('login')
    except Profile.DoesNotExist:
        return redirect('login')

    # Ensure FarmerProfile exists
    farmer_profile, _ = FarmerProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = FarmerProfileForm(request.POST, request.FILES, instance=farmer_profile)
        if form.is_valid():
            form.save()
            return redirect('farmer-dashboard')
    else:
        form = FarmerProfileForm(instance=farmer_profile)

    context = {
        'form': form,
        'profile': profile,  # Profile includes phone, ward, tole
        'farmerprofile': farmer_profile,
        'user': user,
    }
    return render(request, 'accounts/update_farmer_profile.html', context)

@login_required
@customer_required
def update_customer_profile(request):
    user = request.user

    try:
        profile = user.profile
        if profile.role != 'customer':
            return redirect('login')
    except Profile.DoesNotExist:
        return redirect('login')

    # Get or create the CustomerProfile instance
    customer_profile, _ = CustomerProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, request.FILES, instance=profile)  # `request.FILES` added here too
        if form.is_valid():
            form.save()

            # Save names and profile picture in CustomerProfile
            # customer_profile.first_name = request.POST.get('first_name', customer_profile.first_name)
            # customer_profile.last_name = request.POST.get('last_name', customer_profile.last_name)

            if 'profile_picture' in request.FILES:
                customer_profile.profile_picture = request.FILES['profile_picture']

            customer_profile.save()

            return redirect('customer-dashboard')
    else:
        form = CustomerProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
        'customer_profile': customer_profile,
        'user': user,
    }
    return render(request, 'accounts/update_customer_profile.html', context)
