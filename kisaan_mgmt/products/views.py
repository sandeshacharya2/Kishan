from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProductForm
from .models import Product, ProductSynonym  # Make sure ProductSynonym exists
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils.translation import gettext_lazy as _
import requests
from django.conf import settings
from django.db.models import Sum, Count, Min, Max, OuterRef, Subquery
from django.core.mail import send_mail
from django.contrib import messages
from accounts.models import FarmerReview
from django.db.models import Avg
from accounts.views.role_based_redirect import farmer_required, customer_required





def project(request):
    return render(request, 'landingpage/project.html')
def service(request):
    return render(request, 'landingpage/service.html')

def carrers(request):
    return render(request, 'landingpage/careers.html')

# Define Roman and English synonyms
synonyms_dict = {
    "आलु": {"roman": ["aalu", "alu"], "english": ["potato"]},
    "प्याज": {"roman": ["pyaaj", "pyaj"], "english": ["onion"]},
    "लसुन": {"roman": ["lasun"], "english": ["garlic"]},
    "टमाटर": {"roman": ["tamatar"], "english": ["tomato"]},
    "बन्दा": {"roman": ["banda"], "english": ["cabbage"]},
    "काउली": {"roman": ["kauli"], "english": ["cauliflower"]},
    "मुला": {"roman": ["mula"], "english": ["radish"]},
    "गाजर": {"roman": ["gajar"], "english": ["carrot"]},
    "साग": {"roman": ["saag"], "english": ["spinach"]},
    "काक्रो": {"roman": ["kakro"], "english": ["cucumber"]},
    "भेनता": {"roman": ["bheneta"], "english": ["eggplant"]},
    "सिमि": {"roman": ["simi"], "english": ["bean"]},
    "बोडी": {"roman": ["bodi"], "english": ["long bean"]},
    "लौका": {"roman": ["lauka"], "english": ["bottle gourd"]},
    "करेला": {"roman": ["karela"], "english": ["bitter gourd"]},
    "खुर्सानी": {"roman": ["khursani"], "english": ["chili"]},
    "धनिया": {"roman": ["dhaniya"], "english": ["coriander"]},
    "अदुवा": {"roman": ["aduwa"], "english": ["ginger"]},
    "फर्सी": {"roman": ["pharsi"], "english": ["pumpkin"]},
    "चिचिँडो": {"roman": ["chichindo"], "english": ["sponge gourd"]},
    "स्याउ": {"roman": ["syaau", "syau"], "english": ["apple"]},
    "केरा": {"roman": ["kera"], "english": ["banana"]},
    "सुन्तला": {"roman": ["suntala"], "english": ["orange"]},
    "मेवा": {"roman": ["mewa"], "english": ["nuts"]},
    "आँप": {"roman": ["aamp"], "english": ["mango"]},
    "नासपाती": {"roman": ["naspati"], "english": ["pear"]},
    "कागती": {"roman": ["kagati"], "english": ["lemon"]},
    "भुइँकटहर": {"roman": ["bhui katihar"], "english": ["guava"]},
    "धान": {"roman": ["dhan"], "english": ["rice"]},
    "गहुँ": {"roman": ["gahu"], "english": ["wheat"]},
    "मकै": {"roman": ["makai"], "english": ["corn"]},
    "जौ": {"roman": ["jau"], "english": ["barley"]},
    "कोदो": {"roman": ["kodo"], "english": ["millet"]},
    "फापर": {"roman": ["phapar"], "english": ["buckwheat"]},
    "चना": {"roman": ["chana"], "english": ["chickpea"]},
    "मुसुरो": {"roman": ["musuro"], "english": ["lentil"]},
    "मास": {"roman": ["maas"], "english": ["meat"]},
    "स्याल्टुङ": {"roman": ["syaltung"], "english": ["soybean"]},
    "केराउ": {"roman": ["kerau"], "english": ["mustard seed"]},
    "तोरी": {"roman": ["tori"], "english": ["rapeseed"]}
    # Add more as needed
}
@farmer_required
@login_required
def add_product(request):
    farmer = request.user.farmerprofile  #Get farmer profile

    # ✅ Calculate average rating
<<<<<<< HEAD
    avg_rating = FarmerReview.objects.filter(farmer=request.user.farmerprofile).aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating = round(avg_rating, 1)

    # ✅ Fetch reviews from customers
    reviews = FarmerReview.objects.filter(farmer=request.user.farmerprofile).select_related('customer').order_by('-created_at')
=======
    avg_rating = FarmerReview.objects.filter(farmer=farmer).aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating = round(avg_rating, 1)

    # ✅ Fetch reviews from customers
    reviews = FarmerReview.objects.filter(farmer=farmer).select_related('customer').order_by('-created_at')
>>>>>>> fbedd1207d1e8e9530623c6a71375d99dbcb3459

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)

            is_other = False
            if product.sub_category == 'अन्य':
                product.sub_category = request.POST.get('other_subcategory')
                is_other = True

            product.farmer = farmer   #link to the product where current farmer is adding the product
            product.save()

            # Always create Nepali synonym
            ProductSynonym.objects.create(
                product=product,
                language="nepali",
                synonym=product.sub_category
            )

            # Auto-add Roman/English if known
            if product.sub_category in synonyms_dict:
                for roman_name in synonyms_dict[product.sub_category]["roman"]:
                    ProductSynonym.objects.create(product=product, language="roman", synonym=roman_name)
                for eng_name in synonyms_dict[product.sub_category]["english"]:
                    ProductSynonym.objects.create(product=product, language="english", synonym=eng_name)
            else:
                # It's unknown → likely "अन्य" → notify admin
                if is_other:
                    try:
                        farmer_name = request.user.get_full_name() or request.user.username
                        admin_url = request.build_absolute_uri(f"/admin/products/product/{product.id}/change/")

                        send_mail(
                            subject=f'🔔 New Custom Product Added: {product.sub_category}',
                            message=f'''
Hello Admin,

A new custom product has been added by a farmer and needs your attention.

Farmer: {farmer_name}
Product: {product.sub_category}
Quantity: {product.quantity} {product.unit}
Price: {product.price} per unit
Date Posted: {product.date_posted.strftime("%Y-%m-%d %H:%M")}

Please log in to Django Admin and add Roman & English synonyms:
{admin_url}

Thank you!
                            ''',
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[admin[1] for admin in settings.ADMINS],
                            fail_silently=False,
                        )
                    except Exception as e:
                        print("Failed to send admin email:", e)

            return redirect('farmer-dashboard')
    else:
        form = ProductForm()

    return render(request, 'products/add_product.html', {
        'form': form,
        'avg_rating': avg_rating,   # ✅ Pass to template
        'reviews': reviews,         # ✅ Pass to template
    })
@farmer_required
@login_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Only owner can edit
    if product.farmer != request.user.farmerprofile:
        return HttpResponseForbidden(_("You are not allowed to edit this product."))

    # ✅ Calculate average rating
    avg_rating = FarmerReview.objects.filter(farmer=request.user.farmerprofile).aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating = round(avg_rating, 1)

    # ✅ Fetch reviews from customers
    reviews = FarmerReview.objects.filter(farmer=request.user.farmerprofile).select_related('customer').order_by('-created_at')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            updated_product = form.save(commit=False)
            if updated_product.sub_category == 'अन्य':
                updated_product.sub_category = request.POST.get('other_subcategory')
            updated_product.save()
            return redirect('farmer-dashboard')
    else:
        form = ProductForm(instance=product)

    return render(request, 'products/edit_product.html', {
        'form': form,
        'product': product,
        'avg_rating': avg_rating,   # ✅ Pass to template
        'reviews': reviews,         # ✅ Pass to template
    })


@farmer_required

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Only owner can delete
    if product.farmer != request.user.farmerprofile:
        return HttpResponseForbidden(_("You are not allowed to delete this product."))

    # ✅ Calculate average rating
    avg_rating = FarmerReview.objects.filter(farmer=request.user.farmerprofile).aggregate(Avg('rating'))['rating__avg'] or 0
    avg_rating = round(avg_rating, 1)

    # ✅ Fetch reviews from customers
    reviews = FarmerReview.objects.filter(farmer=request.user.farmerprofile).select_related('customer').order_by('-created_at')

    if request.method == 'POST':
        product.delete()
        # messages.success(request, _("Your product has been deleted successfully."))
        return redirect('farmer-dashboard')

    return render(request, 'products/confirm_delete.html', {
        'product': product,
        'avg_rating': avg_rating,   # ✅ Pass to template
        'reviews': reviews,         # ✅ Pass to template
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
    url = f'https://wttr.in/  {city}?format=j1'

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
    url = f'https://wttr.in/  {city}?format=j1'  # j1 means JSON format

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

"""This line queries the database to retrieve all Product objects 
where the farmer field matches the current logged-in user (request.user).
This means each farmer sees only their own products.
The results are ordered by date_posted in descending order (-date_posted), 
so the newest products appear first."""
# @login_required
# def farmer_dashboard_view(request):
#     products = Product.objects.filter(farmer=request.user).order_by('-date_posted')
#     return render(request, 'accounts/farmer_dashboard.html', {'products': products})


# def marketplace_view(request):
#     products = Product.objects.all().order_by('-date_posted')  # 🛠️ FIXED
#     return render(request, 'products/marketplace.html', {'products': products})


"""Product.objects.values_list('main_category', flat=True) returns a list of values for the main_category 
field from all products
.distinct() ensures that the list contains only unique category names, without duplicates.
So, main_categories will contain a list of all unique main categories that have at least one product"""
def category_list_view(request):
    # Get distinct main categories only that have products
    main_categories = Product.objects.values_list('main_category', flat=True).distinct()
    return render(request, 'landingpage/products.html', {
        'main_categories': main_categories
    })



def fruits(request):
    selected_subcategory = request.GET.get('subcategory', '')
    # SELECT DISTINCT sub_category FROM app_product WHERE main_category = 'फलफुल' ORDER BY sub_category ASC;



    all_subcategories = Product.objects.filter(main_category='फलफुल') \
        .values_list('sub_category', flat=True).distinct().order_by('sub_category')  #flat is also like list but it returns without requring a tuple inside it 


    # Get latest image path for each subcategory
    latest_image_subquery = Product.objects.filter(
        sub_category=OuterRef('sub_category'),
        main_category='फलफुल'
    ).order_by('-id').values('image')[:1]

    subcategory_data = (
        Product.objects.filter(main_category='फलफुल')
        .values('sub_category', 'unit')
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
        .values('sub_category',  'unit')
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
        .values('sub_category', 'unit')
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