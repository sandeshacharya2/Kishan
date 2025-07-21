from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from products.models import Product
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
import math


def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great-circle distance between two points on the Earth."""
    R = 6371  # Earth radius in kilometers
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


@login_required
def customer_dashboard_view(request):
    query = request.GET.get('q')
    filter_type = request.GET.get('filter_type')
    distance_filter = request.GET.get('distance_filter')  # expected values: 'nearest', 'farthest', or None

    products = Product.objects.all().order_by('-date_posted')

    if query:
        products = products.filter(sub_category__istartswith=query)

    if filter_type == 'price':
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price and max_price:
            products = products.filter(price__gte=min_price, price__lte=max_price)
        elif min_price:
            products = products.filter(price__gte=min_price)
        elif max_price:
            products = products.filter(price__lte=max_price)

    elif filter_type == 'date':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        if start_date:
            start_date_parsed = parse_date(start_date)
            if start_date_parsed:
                products = products.filter(date_posted__gte=start_date_parsed)
        if end_date:
            end_date_parsed = parse_date(end_date)
            if end_date_parsed:
                products = products.filter(date_posted__lte=end_date_parsed)

    elif filter_type == 'quantity':
        min_quantity = request.GET.get('min_quantity')
        max_quantity = request.GET.get('max_quantity')
        if min_quantity and max_quantity:
            products = products.filter(quantity__gte=min_quantity, quantity__lte=max_quantity)
        elif min_quantity:
            products = products.filter(quantity__gte=min_quantity)
        elif max_quantity:
            products = products.filter(quantity__lte=max_quantity)

    # Get customer profile and location
    customer_profile = getattr(request.user, 'profile', None)

    if customer_profile and customer_profile.latitude is not None and customer_profile.longitude is not None:
        customer_lat = customer_profile.latitude
        customer_lon = customer_profile.longitude

        # Annotate products with distance to customer
        products_with_distance = []
        for product in products:
            farmer_profile = getattr(product.farmer, 'profile', None)
            if farmer_profile and farmer_profile.latitude is not None and farmer_profile.longitude is not None:
                dist = haversine(customer_lat, customer_lon, farmer_profile.latitude, farmer_profile.longitude)
                product.distance = round(dist, 3)  # raw numeric distance in km

                # Add formatted display_distance string (meters if <1km, else km)
                if dist < 1:
                    product.display_distance = f"{round(dist * 1000)} m"
                else:
                    product.display_distance = f"{dist:.2f} km"

                products_with_distance.append((product, dist))
            else:
                product.distance = None
                product.display_distance = None
                products_with_distance.append((product, float('inf')))  # Unknown location pushed to end

        # Sort by distance if requested
        if distance_filter in ['nearest', 'farthest']:
            reverse_sort = True if distance_filter == 'farthest' else False
            products_with_distance.sort(key=lambda x: x[1], reverse=reverse_sort)

        # Extract sorted products
        products = [p[0] for p in products_with_distance]

    else:
        # If customer location not available, set distance and display_distance to None for all products
        for product in products:
            product.distance = None
            product.display_distance = None

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products, 9)
    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    return render(request, 'accounts/customer_dashboard.html', {
        'products': products_page,
        'customer_profile': customer_profile,
        'query': query,
        'filter_type': filter_type,
        'distance_filter': distance_filter,
    })


@login_required
def view_farmer_location(request, farmer_id):
    farmer = get_object_or_404(User, id=farmer_id)
    profile = getattr(farmer, 'profile', None)
    context = {
        'latitude': getattr(profile, 'latitude', 0),
        'longitude': getattr(profile, 'longitude', 0),
        'farmer_name': farmer.username,
    }
    return render(request, 'accounts/view_farmer_location.html', context)
