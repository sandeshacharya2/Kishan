from django.shortcuts import redirect, render
from ..forms import FarmerProfileForm, CustomerProfileForm
from ..models import Profile, FarmerProfile, CustomerProfile
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext_lazy as _
from accounts.views.role_based_redirect import farmer_required, customer_required
from products.models import Product
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from accounts.views.customer_dashboard_view import haversine
from accounts.models import FarmerReview
from django.db.models import Avg


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
        'profile': profile,
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
        # ✅ FIX: Bind form to customer_profile, NOT profile
        form = CustomerProfileForm(request.POST, request.FILES, instance=customer_profile)
        if form.is_valid():
            form.save()
            return redirect('customer-dashboard')
    else:
        # ✅ FIX: Bind form to customer_profile, NOT profile
        form = CustomerProfileForm(instance=customer_profile)

    context = {
        'form': form,
        'profile': profile,
        'customer_profile': customer_profile,
        'user': user,
        'avg_rating': avg_rating,
        'reviews': reviews,
    }
    return render(request, 'accounts/update_customer_profile.html', context)

@login_required
def farmer_detail(request, farmer_id):
    # ✅ FIXED: Use 'user__profile__role' to traverse from FarmerProfile -> User -> Profile -> role
    farmer = get_object_or_404(FarmerProfile, id=farmer_id, user__profile__role="farmer")
    
    # ✅ FIXED: If Product.farmer is ForeignKey to User, use farmer.user
    products = Product.objects.filter(farmer=farmer)

    # ✅ FIXED: Filter reviews by farmer.user, not farmer (FarmerReview.farmer is FK to User)
    avg_rating = FarmerReview.objects.filter(farmer=farmer.user).aggregate(Avg("rating"))["rating__avg"] or 0
    avg_rating = round(avg_rating, 1)

    # Get customer location from CustomerProfile
    try:
        customer_profile = request.user.customerprofile
        customer_lat = customer_profile.latitude
        customer_lon = customer_profile.longitude
    except (CustomerProfile.DoesNotExist, AttributeError):
        customer_lat = customer_lon = None

    # Attach data to each product for the template
    for product in products:
        # Attach farmer avg rating
        product.farmer_avg_rating = avg_rating

        # Get farmer location from FarmerProfile (already have it!)
        farmer_lat = farmer.latitude
        farmer_lon = farmer.longitude

        # Calculate and attach distance
        if customer_lat is not None and customer_lon is not None and farmer_lat is not None and farmer_lon is not None:
            dist = haversine(customer_lat, customer_lon, farmer_lat, farmer_lon)
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