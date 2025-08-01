from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProductForm
from .models import Product
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
<<<<<<< HEAD
from django.utils.translation import gettext_lazy as _
=======
from django.db.models import Sum, Avg, Count
from django.utils.translation import gettext_lazy as _
import requests
>>>>>>> sandesh

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)  # include request.FILES here
        if form.is_valid():
            product = form.save(commit=False)
            if product.sub_category == 'अन्य':
                product.sub_category = request.POST.get('other_subcategory')
            product.farmer = request.user
            product.save()
            return redirect('farmer-dashboard')
    else:
        form = ProductForm()
    return render(request, 'products/add_product.html', {'form': form})

@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Only owner can edit
    if product.farmer != request.user:
        return HttpResponseForbidden(_("You are not allowed to edit this product."))

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)  # include request.FILES here
        if form.is_valid():
            updated_product = form.save(commit=False)
            if updated_product.sub_category == 'अन्य':
                updated_product.sub_category = request.POST.get('other_subcategory')
            updated_product.save()
            return redirect('farmer-dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'products/edit_product.html', {'form': form, 'product': product})

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Only owner can delete
    if product.farmer != request.user:
        return HttpResponseForbidden(_("You are not allowed to delete this product."))

    if request.method == 'POST':
        product.delete()
        return redirect('farmer-dashboard')

    return render(request, 'products/confirm_delete.html', {'product': product})

@login_required
def farmer_dashboard_view(request):
    products = Product.objects.filter(farmer=request.user).order_by('-date_posted')
    return render(request, 'accounts/farmer_dashboard.html', {'products': products})


# def marketplace_view(request):
#     products = Product.objects.all().order_by('-date_posted')  # 🛠️ FIXED
#     return render(request, 'products/marketplace.html', {'products': products})
<<<<<<< HEAD
=======

def category_list_view(request):
    # Get distinct main categories only that have products
    main_categories = Product.objects.values_list('main_category', flat=True).distinct()
    return render(request, 'landingpage/products.html', {
        'main_categories': main_categories
    })

def krishi_news(request):
    return render(request, 'landingpage/krishi_news.html')

def farming_tips(request):
    return render(request, 'landingpage/farming_tips.html')

def tech_updates(request):
    return render(request, 'landingpage/tech_updates.html')

import requests
from django.shortcuts import render

def weather_view(request):
    city = 'Beni, Myagdi'
    url = f'https://wttr.in/{city}?format=j1'

    try:
        response = requests.get(url)
        data = response.json()

        current_condition = data['current_condition'][0]

        raw_icon_url = current_condition['weatherIconUrl'][0]['value'] if current_condition['weatherIconUrl'] else ''
        print("Raw icon URL from API:", raw_icon_url)

        if raw_icon_url and raw_icon_url.startswith("//"):
            icon_url = f"https:{raw_icon_url}"
        else:
            # Use fallback icon
            icon_url = "/static/default_weather_icon.png"  # Make sure you add this image to your static files

        weather = {
            'temperature_c': current_condition['temp_C'],
            'weather_desc': current_condition['weatherDesc'][0]['value'],
            'humidity': current_condition['humidity'],
            'wind_speed_kmph': current_condition['windspeedKmph'],
            'feels_like_c': current_condition['FeelsLikeC'],
            'icon_url': icon_url,
        }

        print("Final icon URL:", icon_url)

    except Exception as e:
        print("Error fetching weather:", e)
        weather = None

    return render(request, 'landingpage/weather_info.html', {'weather': weather, 'city': city})

    city = 'Beni, Myagdi'
    url = f'https://wttr.in/{city}?format=j1'  # j1 means JSON format

    try:
        response = requests.get(url)
        data = response.json()

        # Extract current condition data
        current_condition = data['current_condition'][0]

        weather = {
            'temperature_c': current_condition['temp_C'],
            'weather_desc': current_condition['weatherDesc'][0]['value'],
            'humidity': current_condition['humidity'],
            'wind_speed_kmph': current_condition['windspeedKmph'],
            'feels_like_c': current_condition['FeelsLikeC'],
            'icon_url': f"https:{current_condition['weatherIconUrl'][0]['value']}",
        }
        print("Icon URL:", weather['icon_url'])  # Add this line to print the icon URL


    except Exception as e:
        weather = None
    return render(request, 'landingpage/weather_info.html', {'weather': weather, 'city': city})





from django.conf import settings
from django.db.models import Sum, Count, Min, Max, OuterRef, Subquery
def fruits(request):
    selected_subcategory = request.GET.get('subcategory', '')

    all_subcategories = Product.objects.filter(main_category='फलफुल') \
        .values_list('sub_category', flat=True).distinct().order_by('sub_category')

    # Get latest image path for each subcategory
    latest_image_subquery = Product.objects.filter(
        sub_category=OuterRef('sub_category'),
        main_category='फलफुल'
    ).order_by('-id').values('image')[:1]

    subcategory_data = (
        Product.objects.filter(main_category='फलफुल')
        .values('sub_category', 'sub_category_roman', 'unit')
        .annotate(
            total_quantity=Sum('quantity'),
            min_price=Min('price'),
            max_price=Max('price'),
            product_count=Count('id'),
            latest_image=Subquery(latest_image_subquery)
        )
        .order_by('sub_category')
    )

    if selected_subcategory:
        subcategory_data = [item for item in subcategory_data if item['sub_category'] == selected_subcategory]

    chunks = [subcategory_data[i:i+6] for i in range(0, len(subcategory_data), 6)]

    return render(request, 'landingpage/fruits.html', {
        'chunks': chunks,
        'all_subcategories': all_subcategories,
        'selected_subcategory': selected_subcategory,
        'MEDIA_URL': settings.MEDIA_URL,
    })


def grains(request):
    selected_subcategory = request.GET.get('subcategory', '')

    all_subcategories = Product.objects.filter(main_category='खाद्यान्न') \
        .values_list('sub_category', flat=True).distinct().order_by('sub_category')

    # Get latest image path for each subcategory
    latest_image_subquery = Product.objects.filter(
        sub_category=OuterRef('sub_category'),
        main_category='खाद्यान्न'
    ).order_by('-id').values('image')[:1]

    subcategory_data = (
        Product.objects.filter(main_category='खाद्यान्न')
        .values('sub_category', 'sub_category_roman', 'unit')
        .annotate(
            total_quantity=Sum('quantity'),
            min_price=Min('price'),
            max_price=Max('price'),
            product_count=Count('id'),
            latest_image=Subquery(latest_image_subquery)
        )
        .order_by('sub_category')
    )

    if selected_subcategory:
        subcategory_data = [item for item in subcategory_data if item['sub_category'] == selected_subcategory]

    chunks = [subcategory_data[i:i+6] for i in range(0, len(subcategory_data), 6)]

    return render(request, 'landingpage/grains.html', {
        'chunks': chunks,
        'all_subcategories': all_subcategories,
        'selected_subcategory': selected_subcategory,
        'MEDIA_URL': settings.MEDIA_URL,
    })

def vegetables(request):
    selected_subcategory = request.GET.get('subcategory', '')

    all_subcategories = Product.objects.filter(main_category='तरकारी') \
        .values_list('sub_category', flat=True).distinct().order_by('sub_category')

    # Get latest image path for each subcategory
    latest_image_subquery = Product.objects.filter(
        sub_category=OuterRef('sub_category'),
        main_category='तरकारी'
    ).order_by('-id').values('image')[:1]

    subcategory_data = (
        Product.objects.filter(main_category='तरकारी')
        .values('sub_category', 'sub_category_roman', 'unit')
        .annotate(
            total_quantity=Sum('quantity'),
            min_price=Min('price'),
            max_price=Max('price'),
            product_count=Count('id'),
            latest_image=Subquery(latest_image_subquery)
        )
        .order_by('sub_category')
    )

    if selected_subcategory:
        subcategory_data = [item for item in subcategory_data if item['sub_category'] == selected_subcategory]

    chunks = [subcategory_data[i:i+6] for i in range(0, len(subcategory_data), 6)]

    return render(request, 'landingpage/vegetables.html', {
        'chunks': chunks,
        'all_subcategories': all_subcategories,
        'selected_subcategory': selected_subcategory,
        'MEDIA_URL': settings.MEDIA_URL,
    })
>>>>>>> sandesh
