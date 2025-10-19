from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    # Customer purchase flow
    path('<int:product_id>/buy/', views.choose_quantity, name='choose_quantity'),          
    path('<int:product_id>/payment-request/', views.payment_request, name='payment_request'),  # eSewa
    path('<int:product_id>/cod/', views.cod_payment, name='cod_payment'),  # Cash on Delivery
    path('<int:product_id>/payment-selection/', views.payment_selection, name='payment_selection'),
# path('<int:product_id>/cod-payment/', views.cod_payment, name='cod_payment'),

    # eSewa payment callbacks
    path('success/', views.payment_success, name='payment_success'),
    path('failure/', views.payment_failure, name='payment_failure'),

    # Farmer income dashboard
    path('transaction-list/', views.transaction_list, name='transaction-list'),

    # Customer purchases
    path('my-purchases/', views.customer_purchases, name='customer_purchases'),

    # Farmer updates delivery status
    path('update-delivery-status/<int:transaction_id>/', views.update_delivery_status, name='update_delivery_status'),

    # Customer confirms delivery
    path('confirm-delivery/<int:transaction_id>/', views.confirm_delivery, name='confirm-delivery'),

    # Customer disputes delivery
    path('dispute-delivery/<int:transaction_id>/', views.dispute_delivery, name='dispute-delivery'),
    path('cod-pay/<int:transaction_id>/', views.cod_pay, name='cod_pay'),
    path('confirm-cod/<int:transaction_id>/', views.confirm_cod_payment, name='confirm_cod_payment'),
    path('income-summary/', views.income_summary, name='income_summary'),

]
