from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path('<int:product_id>/buy/', views.choose_quantity, name='choose_quantity'),          # quantity form
    path('<int:product_id>/payment-request/', views.payment_request, name='payment_request'),  # process payment POST
    path('success/', views.payment_success, name='payment_success'),
    path('failure/', views.payment_failure, name='payment_failure'),
    path('income-summary/', views.income_summary, name='income_summary'),
    path('my-purchases/', views.customer_purchases, name='customer_purchases'),

]
