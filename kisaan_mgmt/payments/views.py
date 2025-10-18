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
from django.db.models import Avg
from django.contrib import messages

@customer_required
def choose_quantity(request, product_id):
    try:
        product = get_object_or_404(Product, pk=product_id)
        if request.method == 'POST':
            try:
                qty = float(request.POST.get('quantity', 1))
            except (TypeError, ValueError):
                qty = 1
            if qty < 1 or qty > product.quantity:
                qty = 1
            
            amount = product.price * qty
            pid = get_random_string(10)  # random payment ID

            # Pass data to payment choice page
            context = {
                'product': product,
                'quantity': qty,
                'amount': amount,
                'pid': pid,
            }
            return render(request, 'payments/payment_choice.html', context)
        else:
            return render(request, 'payments/choose_quantity.html', {'product': product})
    except Exception as e:
        print("❌ Error in choose_quantity:", e)
        return render(request, 'payments/error.html', {'message': 'Unable to load product.'})


@csrf_exempt
def payment_request(request, product_id):
    try:
        product = get_object_or_404(Product, pk=product_id)

        if request.method == 'POST':
            qty = float(request.POST.get('quantity', 1))
            if qty < 1 or qty > product.quantity:
                qty = 1

            amount = product.price * qty
            payment_method = request.POST.get('payment_method')  # 'Esewa' or 'COD'

            if payment_method == 'COD':
                # 🔸 Save transaction immediately
                transaction = Transaction.objects.create(
                    user=request.user,
                    product=product,
                    amount=amount,
                    quantity=qty,
                    payment_method='COD',
                    payment_status='Pending',   # COD starts as pending
                    delivery_status='Pending',
                )

                # Reduce stock immediately
                product.quantity -= qty
                if product.quantity < 0:
                    product.quantity = 0
                product.save()

                #Show confirmation page instead of redirecting
                return render(request, 'payments/cod_confirmation.html', {
                    'transaction': transaction,
                })

            else:  # eSewa payment
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
                payment_method='eSewa',
                payment_status='Success',  # ✅ now use payment_status
                delivery_status='Pending',
)

                
            except Exception as e:
                print("❌ Error saving transaction:", e)
                # Handle or log as needed

            # ✅ Send email to farmer with buyer details
            try:
                farmer = product.farmer.user # assuming FK to User
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


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
# from ..models import Transaction, FarmerReview
from accounts.views.role_based_redirect import farmer_required
from django.shortcuts import render
from django.db.models import Sum, Avg, Q, Count
from .models import Transaction  # Import your Transaction model
from accounts.models import FarmerProfile  # Import your FarmerProfile model

def income_summary(request):
    # Get the logged-in farmer's profile
    farmer_profile = request.user.farmerprofile
    print(f"User Profile: {farmer_profile}")  # This matches your log

    # Calculate total income
    total_income = Transaction.objects.filter(
        product__farmer=farmer_profile
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Calculate average rating (assuming you have a Review model)
    avg_rating = FarmerReview.objects.filter(
        farmer=farmer_profile  # Assuming farmer is the User object
    ).aggregate(avg=Avg('rating'))['avg'] or 0

    # Calculate counts
    completed_count = Transaction.objects.filter(
        product__farmer=farmer_profile,
        delivery_status='Completed'
    ).count()
    print(f"Completed: {completed_count}")  # This matches your log

    pending_count = Transaction.objects.filter(
        product__farmer=farmer_profile,
        delivery_status='Pending'
    ).count()
    print(f"Pending: {pending_count}")  # This matches your log

    # Fetch all transactions for the table
    all_transactions = Transaction.objects.filter(
        product__farmer=farmer_profile
    ).select_related('product', 'user').order_by('-created_at')

    # Pass ALL variables to the template context
    context = {
        'total_income': total_income,
        'avg_rating': round(avg_rating, 1),  # Round to 1 decimal place
        'completed_count': completed_count,
        'pending_count': pending_count,
        'all_transactions': all_transactions,
    }

    return render(request, 'payments/income_summary.html', context)  # Adjust template path as needed
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.conf import settings

from payments.models import Transaction
from products.models import Product
from accounts.views.role_based_redirect import farmer_required, customer_required


@login_required
@farmer_required
def update_delivery_status(request, transaction_id):
    try:
        # product__farmer expects FarmerProfile → use request.user.farmerprofile
        transaction = get_object_or_404(Transaction, pk=transaction_id, product__farmer=request.user.farmerprofile)
        if request.method == 'POST':
            new_status = request.POST.get('delivery_status')
            if new_status in ['Dispatched', 'Delivered']:
                transaction.delivery_status = new_status
                transaction.save()
        return redirect('payments:income_summary')
    except Exception as e:
        print("❌ Error updating delivery status:", e)
        return render(request, 'payments/error.html', {'message': 'Cannot update delivery status.'})


@login_required
@customer_required
def confirm_delivery(request, transaction_id):
    # user expects User → use request.user, NOT request.user.customerprofile
    transaction = get_object_or_404(Transaction, pk=transaction_id, user=request.user)

    if request.method == 'POST' and transaction.delivery_status == 'Delivered':
        transaction.delivery_status = 'Completed'

        if transaction.payment_method == 'COD' and transaction.payment_status == 'Pending':
            # Customer confirms delivery, now they must pay
            transaction.payment_status = 'Pay'

        transaction.save()

    return redirect('payments:customer_purchases')


@login_required
@farmer_required
def confirm_cod_payment(request, transaction_id):
    # product__farmer expects FarmerProfile → use request.user.farmerprofile
    transaction = get_object_or_404(Transaction, pk=transaction_id, product__farmer=request.user.farmerprofile)

    if request.method == 'POST' and transaction.payment_method == 'COD' and transaction.payment_status == 'Waiting':
        transaction.payment_status = 'Success'
        transaction.save()

    return redirect('payments:income_summary')


@login_required
@customer_required
def dispute_delivery(request, transaction_id):
    try:
        # user expects User → use request.user
        transaction = get_object_or_404(Transaction, pk=transaction_id, user=request.user)
        if request.method == 'POST' and transaction.delivery_status == 'Delivered':
            transaction.delivery_status = 'Dispute'
            transaction.save()

            # ✅ Notify admin
            try:
                admin_email = settings.DEFAULT_FROM_EMAIL
                subject = f"⚠️ Dispute Alert: Transaction {transaction.pid}"
                message = (
                    f"Customer {request.user.username} has marked the product "
                    f"'{transaction.product.sub_category}' (PID: {transaction.pid}) as Not Received.\n\n"
                    f"Farmer: {transaction.product.farmer.user.username}\n"  # ✅ farmer is FarmerProfile → access .user
                    f"Quantity: {transaction.quantity}\n"
                    f"Amount: Rs. {transaction.amount}\n"
                    f"Date: {transaction.created_at.strftime('%Y-%m-%d')}\n\n"
                    f"Please review and take necessary action."
                )

                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [admin_email],
                    fail_silently=True,
                )
            except Exception as e:
                print("❌ Error sending admin notification:", e)

        return redirect('payments:customer_purchases')
    except Exception as e:
        print("❌ Error in dispute_delivery:", e)
        return render(request, 'payments/error.html', {'message': 'Cannot mark as dispute.'})


@customer_required
def customer_purchases(request):
    try:
        # user expects User → use request.user
        # Order by newest first → '-created_at'
        transactions = Transaction.objects.filter(user=request.user).select_related('product', 'product__farmer').order_by('-created_at')

        return render(request, 'payments/purchases.html', {
            'transactions': transactions,
        })
    except Exception as e:
        print("❌ Error in customer_purchases:", e)
        return render(request, 'payments/error.html', {'message': 'Error loading purchase history.'})


@customer_required
def payment_selection(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method == "POST":
        qty = int(request.POST.get("quantity", 1))
        amount = product.price * qty

        request.session['payment_qty'] = qty

        return render(request, "payments/payment_choice.html", {
            'product': product,
            'quantity': qty,
            'amount': amount
        })
    else:
        return redirect('payments:choose_quantity', product_id=product.id)


@customer_required
def cod_payment(request, product_id):
    try:
        product = get_object_or_404(Product, pk=product_id)
        qty = float(request.POST.get('quantity', 1))
        amount = product.price * qty
        pid = get_random_string(10)

        product.quantity -= qty
        if product.quantity < 0:
            product.quantity = 0
        product.save()

        # user expects User → use request.user
        Transaction.objects.create(
            user=request.user,
            product=product,
            pid=pid,
            rid='COD',
            amount=amount,
            quantity=qty,
            payment_method='COD',
            payment_status='Pending',
            delivery_status='Pending',
        )

        return redirect('payments:customer_purchases')

    except Exception as e:
        print("❌ Error in COD payment:", e)
        return render(request, 'payments/error.html', {'message': 'COD Payment Failed.'})


@login_required
@customer_required
def cod_pay(request, transaction_id):
    try:
        # user expects User → use request.user
        transaction = get_object_or_404(Transaction, pk=transaction_id, user=request.user)

        if request.method == 'POST' and transaction.payment_method == 'COD' and transaction.payment_status == 'Pay':
            transaction.payment_status = 'Waiting'
            transaction.save()

        return redirect('payments:customer_purchases')

    except Exception as e:
        print("❌ Error in cod_pay:", e)
        messages.error(request, "Cannot process COD payment.")
        return redirect('payments:customer_purchases')