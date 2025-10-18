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
    # Get the FarmerProfile (correct)
    farmer_profile = request.user.farmerprofile

    # No need to re-check role — @farmer_required already ensures it

    # Calculate rating using FarmerProfile (NOT User)
    avg_rating = FarmerReview.objects.filter(farmer=farmer_profile).aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating = round(avg_rating, 1)

    reviews = FarmerReview.objects.filter(farmer=farmer_profile).select_related('customer').order_by('-created_at')

    if request.method == 'POST':
        form = FarmerProfileForm(request.POST, request.FILES, instance=farmer_profile)
        if form.is_valid():
            form.save()
            # messages.success(request, _("Profile updated successfully!"))
            return redirect('farmer-dashboard')
    else:
        form = FarmerProfileForm(instance=farmer_profile)

    context = {
        'form': form,
        'farmerprofile': farmer_profile,
        'avg_rating': avg_rating,
        'reviews': reviews,
    }
    return render(request, 'accounts/update_farmer_profile.html', context)
@login_required
@customer_required
def update_customer_profile(request):
    customer_profile = request.user.customerprofile

    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, request.FILES, instance=customer_profile)
        if form.is_valid():
            form.save()
            # messages.success(request, _("Profile updated successfully!"))
            return redirect('customer-dashboard')
    else:
        form = CustomerProfileForm(instance=customer_profile)

    return render(request, 'accounts/update_customer_profile.html', {'form': form})

@login_required
def farmer_detail(request, farmer_id):
    # Use 'user__profile__role' to traverse from FarmerProfile -> User -> Profile -> role
    farmer = get_object_or_404(FarmerProfile, id=farmer_id, user__profile__role="farmer")
    
    # If Product.farmer is ForeignKey to User, use farmer.user
    products = Product.objects.filter(farmer=farmer)

    #  Filter reviews by farmer.user, not farmer (FarmerReview.farmer is FK to User)
    avg_rating = FarmerReview.objects.filter(farmer=farmer.user.farmerprofile).aggregate(Avg("rating"))["rating__avg"] or 0
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