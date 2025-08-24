from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
import requests
import xml.etree.ElementTree as ET
from products.models import Product  # Adjust if your product model is elsewhere
from payments.models import Transaction  # 🔸 Import the Transaction model
from accounts.views.role_based_redirect import farmer_required, customer_required
from accounts.models import FarmerReview
from accounts.views.update_farmer_profile import FarmerReview
from django.db.models import Avg

@customer_required
def choose_quantity(request, product_id):
    try:
        product = get_object_or_404(Product, pk=product_id)
        return render(request, 'payments/choose_quantity.html', {'product': product})
    except Exception as e:
        print("❌ Error in choose_quantity:", e)
        return render(request, 'payments/error.html', {'message': 'Unable to load product.'})


@csrf_exempt
# @login_required
def payment_request(request, product_id):
    try:
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
    except Exception as e:
        print("❌ Error in payment_request:", e)
        return render(request, 'payments/error.html', {'message': 'Error processing payment request.'})


@csrf_exempt
# @login_required

def payment_success(request):
    try:
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
        except Exception as e:
            print("❌ Error parsing eSewa response:", e)
            return render(request, 'payments/failure.html', {'pid': pid})

        if status == 'Success':
            try:
                qty_num = float(qty)
            except (TypeError, ValueError):
                qty_num = 0

            try:
                product = get_object_or_404(Product, pk=product_id)
                product.quantity -= qty_num
                if product.quantity < 0:
                    product.quantity = 0
                product.save()
            except Exception as e:
                print("❌ Error updating product quantity:", e)
                # Optionally continue to save transaction even if product update fails

            # 🔸 Save the transaction
            try:
                Transaction.objects.create(
                    user=request.user,
                    product=product,
                    pid=pid,
                    rid=rid,
                    amount=amt,
                    quantity=qty_num,
                    status='Success',
                )
            except Exception as e:
                print("❌ Error saving transaction:", e)
                # Handle or log as needed

            # ✅ Send email to farmer with buyer details
            try:
                farmer = product.farmer  # assuming FK to User
                customer = request.user

                try:
                    phone = customer.profile.phonenumber
                except:
                    phone = 'N/A'

                subject = f"✅ Your Product '{product.sub_category}' Has Been Sold!"
                message = (
                    f"Dear {farmer.username},\n\n"
                    f"Your product '{product.sub_category}' has just been purchased.\n\n"
                    f"📦 Quantity: {qty_num}\n"
                    f"💰 Amount: Rs. {amt}\n\n"
                    f"👤 Customer Info:\n"
                    f"Username: {customer.username}\n"
                    f"Email: {customer.email}\n"
                    f"Phone: {phone}\n\n"
                    f"Please prepare for delivery and coordinate accordingly.\n\n"
                    f"Thank you,\n"
                    f"Your Platform Team"
                )

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [farmer.email],
                    fail_silently=True,
                )
            except Exception as e:
                print("❌ Error sending email:", e)

            return render(request, 'payments/success.html', {
                'pid': pid,
                'amount': amt,
                'quantity': qty_num,
                'product': product
            })
        else:
            return render(request, 'payments/failure.html', {'pid': pid})
    except Exception as e:
        print("❌ Unexpected error in payment_success:", e)
        return render(request, 'payments/failure.html', {'pid': request.GET.get('pid')})


@csrf_exempt
# @login_required
def payment_failure(request):
    try:
        return render(request, 'payments/failure.html')
    except Exception as e:
        print("❌ Error in payment_failure:", e)
        return render(request, 'payments/error.html', {'message': 'Error displaying failure page.'})


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
import json
from payments.models import Transaction


@login_required
@farmer_required
def income_summary(request):
    try:
        user = request.user
        
        # Filter transactions for products where the logged-in user is the farmer
        transactions = Transaction.objects.filter(product__farmer=user, status='Success').order_by('-created_at')
        avg_rating = FarmerReview.objects.filter(farmer=user).aggregate(Avg('rating'))['rating__avg'] or 0
        avg_rating = round(avg_rating, 1)

    # ✅ Fetch reviews from customers
        reviews = FarmerReview.objects.filter(farmer=user).select_related('customer').order_by('-created_at')

        # Calculate total income
        total_income = sum(t.amount for t in transactions)

        context = {
            'transactions': transactions,
            'total_income': total_income,
            'reviews': reviews,
            'avg_rating': avg_rating,

        }
        return render(request, 'payments/income_summary.html', context)
    except Exception as e:
        print("❌ Error in income_summary:", e)
        return render(request, 'payments/error.html', {'message': 'Error loading income summary.'})

@customer_required
def customer_purchases(request):
    try:
        user = request.user
        transactions = Transaction.objects.filter(user=request.user).select_related('product', 'product__farmer')

        return render(request, 'payments/purchases.html', {
            'transactions': transactions
        })
    except Exception as e:
        print("❌ Error in customer_purchases:", e)
        return render(request, 'payments/error.html', {'message': 'Error loading purchase history.'})
