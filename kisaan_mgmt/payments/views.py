from django.shortcuts import render, redirect, get_object_or_404
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils.safestring import mark_safe
import json
import requests
import xml.etree.ElementTree as ET
from django.utils.translation import gettext_lazy as _

# Local models
from accounts.models import FarmerReview
from accounts.views.role_based_redirect import farmer_required, customer_required
from accounts.views.update_farmer_profile import FarmerReview 
from products.models import Product
from payments.models import Transaction
from accounts.models import FarmerProfile

# Aggregation
from django.db.models import Avg, Sum, Count, Q
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
            pid = get_random_string(10)  # random payment ID will be genereted  but shown same for farmer and customer

            
            #sending these data to ui 
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
        return render(request, 'payments/error.html', {'message': _('Unable to load product.')})


@csrf_exempt
def payment_request(request, product_id):
    try:
        product = get_object_or_404(Product, pk=product_id)


#checking the choosen quantitty is less than available quantity or not
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
        return render(request, 'payments/error.html', {'message': _('Error processing payment request.')})


@csrf_exempt
# @login_required

def payment_success(request):
    try:
        pid = request.GET.get('pid')
        rid = request.GET.get('refId')
        amt = request.GET.get('amt')
        qty = request.GET.get('qty')
        product_id = request.GET.get('product_id')

        verify_url = "https://rc.esewa.com.np/epay/transrec  "
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
                farmer = product.farmer.user # assuming FK to User → ✅ correct: product.farmer is FarmerProfile
                customer = request.user

                try:
                    phone = customer.profile.phonenumber
                except:
                    phone = 'N/A'

                subject = _("✅ Your Product '%(product_name)s' Has Been Sold!") % {'product_name': product.sub_category}
                message = _(
                    "Dear %(farmer_username)s,\n\n"
                    "Your product '%(product_name)s' has just been purchased.\n\n"
                    "📦 Quantity: %(quantity)s\n"
                    "💰 Amount: Rs. %(amount)s\n\n"
                    "👤 Customer Info:\n"
                    "Username: %(customer_username)s\n"
                    "Email: %(customer_email)s\n"
                    "Phone: %(phone)s\n\n"
                    "Please prepare for delivery and coordinate accordingly.\n\n"
                    "Thank you,\n"
                    "Your Platform Team"
                ) % {
                    'farmer_username': farmer.username,
                    'product_name': product.sub_category,
                    'quantity': qty_num,
                    'amount': amt,
                    'customer_username': customer.username,
                    'customer_email': customer.email,
                    'phone': phone,
                }

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
        return render(request, 'payments/error.html', {'message': _('Error displaying failure page.')})


def transaction_list(request):
    # Get the logged-in farmer's profile
    # ✅ CORRECTED: request.user.farmerprofile is already FarmerProfile
    farmer_profile = request.user.farmerprofile
    print(f"User Profile: {farmer_profile}")  # This matches your log
    avg_rating = FarmerReview.objects.filter(farmer=farmer_profile).aggregate(avg=Avg('rating'))['avg'] or 0

    # Calculate total income

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
         # Round to 1 decimal place
        'completed_count': completed_count,
        'pending_count': pending_count,
        'all_transactions': all_transactions,
        'avg_rating': round(avg_rating, 1),

    }

    return render(request, 'payments/transaction_list.html', context)  # Adjust template path as needed
from django.db.models import Sum, Avg, F, FloatField
from django.db.models.functions import Cast
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from django.shortcuts import render
from .models import Transaction
from accounts.models import FarmerReview  # Adjust if needed

from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Sum, Avg, F, FloatField
from django.db.models.functions import Cast
from django.utils import timezone
from django.shortcuts import render
from payments.models import Transaction


def income_summary(request):
    farmer = request.user.farmerprofile

    # ✅ Only successful payments
    transactions = Transaction.objects.filter(
        product__farmer=farmer,
        payment_status='Success'
    )

    # Date filters
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    start_date = end_date = None
    if start_date_str:
        try:
            start_date = date.fromisoformat(start_date_str)
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date = date.fromisoformat(end_date_str)
        except ValueError:
            pass

    filtered_transactions = transactions
    if start_date:
        filtered_transactions = filtered_transactions.filter(created_at__date__gte=start_date)
    if end_date:
        filtered_transactions = filtered_transactions.filter(created_at__date__lte=end_date)

    # Exclude zero quantity (avoid division errors)
    filtered_transactions = filtered_transactions.filter(quantity__gt=0)

    # Helper to safely sum
    def safe_sum(queryset):
        total = queryset.aggregate(total=Sum('amount'))['total']
        return total if total is not None else Decimal('0.00')

    now = timezone.now()
    today = now.date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)

    # ✅ Income calculations only from successful transactions
    total_income = safe_sum(transactions)
    daily_income = safe_sum(transactions.filter(created_at__date=today))
    weekly_income = safe_sum(transactions.filter(created_at__date__gte=start_of_week))
    monthly_income = safe_sum(transactions.filter(created_at__date__gte=start_of_month))
    yearly_income = safe_sum(transactions.filter(created_at__date__gte=start_of_year))
    filtered_income = safe_sum(filtered_transactions)

    avg_rating = FarmerReview.objects.filter(farmer=farmer).aggregate(avg=Avg('rating'))['avg'] or 0

    # ✅ Include payment_status for UI
    transaction_details = filtered_transactions.select_related(
        'product', 'user'
    ).annotate(
        price_per_unit=Cast(F('amount') / F('quantity'), FloatField())
    ).values(
        'id',
        'product__sub_category',
        'quantity',
        'amount',
        'price_per_unit',
        'user__first_name',
        'user__last_name',
        'payment_status',  # ✅ Include this field
        'created_at'
    ).order_by('-created_at')

    context = {
        'total_income': total_income,
        'daily_income': daily_income,
        'weekly_income': weekly_income,
        'monthly_income': monthly_income,
        'yearly_income': yearly_income,
        'filtered_income': filtered_income,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'avg_rating': round(avg_rating, 1),
        'transactions': transaction_details,
    }

    return render(request, 'payments/income_summary.html', context)

    farmer = request.user.farmerprofile
    transactions = Transaction.objects.filter(product__farmer=farmer)

    # Get date filters
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    start_date = end_date = None
    if start_date_str:
        try:
            start_date = date.fromisoformat(start_date_str)
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date = date.fromisoformat(end_date_str)
        except ValueError:
            pass

    filtered_transactions = transactions
    if start_date:
        filtered_transactions = filtered_transactions.filter(created_at__date__gte=start_date)
    if end_date:
        filtered_transactions = filtered_transactions.filter(created_at__date__lte=end_date)

    # Exclude zero quantity to avoid division issues
    filtered_transactions = filtered_transactions.filter(quantity__gt=0)

    def safe_sum(queryset):
        total = queryset.aggregate(total=Sum('amount'))['total']
        return total if total is not None else Decimal('0.00')

    now = timezone.now()
    today = now.date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    start_of_year = today.replace(month=1, day=1)

    total_income = safe_sum(transactions)
    daily_income = safe_sum(transactions.filter(created_at__date=today))
    weekly_income = safe_sum(transactions.filter(created_at__date__gte=start_of_week))
    monthly_income = safe_sum(transactions.filter(created_at__date__gte=start_of_month))
    yearly_income = safe_sum(transactions.filter(created_at__date__gte=start_of_year))
    filtered_income = safe_sum(filtered_transactions)

    avg_rating = FarmerReview.objects.filter(farmer=farmer).aggregate(avg=Avg('rating'))['avg'] or 0

    # ✅ Correct annotation with explicit FloatField
    transaction_details = filtered_transactions.select_related(
        'product', 'user'
    ).annotate(
        price_per_unit=Cast(F('amount') / F('quantity'), FloatField())
    ).values(
        'id',
        'product__sub_category',
        'quantity',
        'amount',
        'price_per_unit',
        'user__first_name',
        'user__last_name',
        'created_at'
    ).order_by('-created_at')

    context = {
        'total_income': total_income,
        'daily_income': daily_income,
        'weekly_income': weekly_income,
        'monthly_income': monthly_income,
        'yearly_income': yearly_income,
        'filtered_income': filtered_income,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'avg_rating': round(avg_rating, 1),
        'transactions': transaction_details,
    }

    return render(request, 'payments/income_summary.html', context)
    return render(request, 'payments/income_summary.html', context)
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
        return render(request, 'payments/error.html', {'message': _('Cannot update delivery status.')})


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
                subject = _(" Dispute Alert: Transaction %(pid)s") % {'pid': transaction.pid}
                message = _(
                    "Customer %(customer_username)s has marked the product "
                    "'%(product_name)s' (PID: %(pid)s) as Not Received.\n\n"
                    "Farmer: %(farmer_username)s\n"  # ✅ farmer is FarmerProfile → access .user
                    "Quantity: %(quantity)s\n"
                    "Amount: Rs. %(amount)s\n"
                    "Date: %(date)s\n\n"
                    "Please review and take necessary action."
                ) % {
                    'customer_username': request.user.username,
                    'product_name': transaction.product.sub_category,
                    'pid': transaction.pid,
                    'farmer_username': transaction.product.farmer.user.username,
                    'quantity': transaction.quantity,
                    'amount': transaction.amount,
                    'date': transaction.created_at.strftime('%Y-%m-%d'),
                }

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
        return render(request, 'payments/error.html', {'message': _('Cannot mark as dispute.')})


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
        return render(request, 'payments/error.html', {'message': _('Error loading purchase history.')})


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
        return render(request, 'payments/error.html', {'message': _('COD Payment Failed.')})


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
        messages.error(request, _("Cannot process COD payment."))
        return redirect('payments:customer_purchases')