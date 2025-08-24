from django.shortcuts import redirect, render
from ..forms import FarmerProfileForm
from ..models import Profile, FarmerProfile
from django.contrib.auth.decorators import login_required
from ..forms import CustomerProfileForm
from ..models import CustomerProfile
from django.utils.translation import gettext_lazy as _
from accounts.views.role_based_redirect import farmer_required, customer_required
from products.models import Product
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required        
from django.contrib.auth.models import User
from accounts.views.customer_dashboard_view import haversine


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
    avg_rating = FarmerReview.objects.filter(farmer=user).aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating = round(avg_rating, 1)

    # ✅ Fetch reviews from customers
    reviews = FarmerReview.objects.filter(farmer=user).select_related('customer').order_by('-created_at')

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
        'avg_rating': avg_rating,
        'reviews': reviews,
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
    avg_rating = FarmerReview.objects.filter(farmer=user).aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating = round(avg_rating, 1)

    # ✅ Fetch reviews from customers
    reviews = FarmerReview.objects.filter(farmer=user).select_related('customer').order_by('-created_at')

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
        'avg_rating': avg_rating,
        'reviews': reviews,
    }
    return render(request, 'accounts/update_customer_profile.html', context)

from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from products.models import Product
from accounts.models import FarmerReview
import math

# Use your existing haversine() function

@login_required
def farmer_detail(request, farmer_id):
    farmer = get_object_or_404(User, id=farmer_id, profile__role="farmer")
    products = Product.objects.filter(farmer=farmer)

    # Farmer's average rating
    avg_rating = FarmerReview.objects.filter(farmer=farmer).aggregate(Avg("rating"))["rating__avg"] or 0
    avg_rating = round(avg_rating, 1)

    # Customer location (if available)
    customer_profile = getattr(request.user, 'profile', None)
    customer_lat = getattr(customer_profile, 'latitude', None)
    customer_lon = getattr(customer_profile, 'longitude', None)

    for product in products:
        # Attach farmer avg rating (same for all this farmer’s products)
        product.farmer_avg_rating = avg_rating

        # Attach distance
        farmer_profile = getattr(product.farmer, 'profile', None)
        if customer_lat and customer_lon and farmer_profile and farmer_profile.latitude and farmer_profile.longitude:
            dist = haversine(customer_lat, customer_lon, farmer_profile.latitude, farmer_profile.longitude)
            product.distance = round(dist, 3)
            product.display_distance = f"{round(dist * 1000)} m" if dist < 1 else f"{dist:.2f} km"
        else:
            product.distance = None
            product.display_distance = None

    context = {
        "farmer": farmer,
        "products": products,
        "avg_rating": avg_rating,
    }
    return render(request, "accounts/farmer_detail.html", context)
