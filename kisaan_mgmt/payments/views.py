from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
import requests
import xml.etree.ElementTree as ET
from products.models import Product  # Adjust if your product model is elsewhere

def choose_quantity(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    return render(request, 'payments/choose_quantity.html', {'product': product})

@csrf_exempt
def payment_request(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        try:
            qty = float(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            qty = 1

        # Validate quantity
        if qty < 1 or qty > product.quantity:
            qty = 1  # fallback safe value

        amount = product.price * qty
        pid = get_random_string(10)

        context = {
            'amount': amount,
            'tax': 0,
            'psc': 0,
            'pdc': 0,
            'total': amount,
            'pid': pid,
            'success_url': f'http://localhost:8000/payments/success/?pid={pid}&qty={qty}&product_id={product.id}',
            'failure_url': 'http://localhost:8000/payments/failure/',
            'merchant_code': 'EPAYTEST',
            'product': product,
            'quantity': qty,
        }
        return render(request, 'payments/esewa_redirect.html', context)
    else:
        return redirect('payments:choose_quantity', product_id=product.id)

@csrf_exempt
def payment_success(request):
    pid = request.GET.get('pid')
    rid = request.GET.get('refId')
    amt = request.GET.get('amt')
    qty = request.GET.get('qty')
    product_id = request.GET.get('product_id')

    verify_url = "https://rc.esewa.com.np/epay/transrec"
    data = {
        'amt': amt,
        'scd': 'EPAYTEST',
        'pid': pid,
        'rid': rid,
    }

    response = requests.post(verify_url, data=data)
    print("🧾 eSewa Verification Response:", response.text)

    try:
        root = ET.fromstring(response.text)
        status = root.find('response_code').text.strip()
        if status == 'Success':
            # Reduce product quantity
            try:
                qty_num = float(qty)
            except (TypeError, ValueError):
                qty_num = 0

            product = get_object_or_404(Product, pk=product_id)
            product.quantity -= qty_num
            if product.quantity < 0:
                product.quantity = 0
            product.save()

            return render(request, 'payments/success.html', {'pid': pid, 'amount': amt, 'quantity': qty_num, 'product': product})
        else:
            return render(request, 'payments/failure.html', {'pid': pid})
    except Exception as e:
        print("❌ Error parsing eSewa response:", e)
        return render(request, 'payments/failure.html', {'pid': pid})

@csrf_exempt
def payment_failure(request):
    return render(request, 'payments/failure.html')
