from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from products.models import Product
@login_required
def customer_dashboard_view(request):
    products = Product.objects.all().order_by('-date_posted')  # or any filter you want

    try:
        customer_profile = request.user.customerprofile
    except:
        customer_profile = None  # fallback if needed

    return render(request, 'accounts/customer_dashboard.html', {
        'products': products,
        'customer_profile': customer_profile,
    })