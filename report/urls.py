# reports/urls.py
from django.urls import path
from .views import submit_farmer_report, submit_customer_report

app_name = 'reports'

urlpatterns = [
    path('farmer/', submit_farmer_report, name='submit_farmer_report'),
    path('customer/', submit_customer_report, name='submit_customer_report'),
]