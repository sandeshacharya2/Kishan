from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProductForm
from .models import Product
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.utils.translation import gettext_lazy as _

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
        return HttpResponseForbidden("You are not allowed to edit this product.")

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
        return HttpResponseForbidden("You are not allowed to delete this product.")

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
