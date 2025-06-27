# accounts/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls import reverse_lazy
from django.contrib.auth.views import LogoutView

from .views import (
    signup_view, verify_otp_view, role_based_redirect,
    farmer_dashboard_view, customer_dashboard_view,
    FarmerLoginView, CustomerLoginView
)


# from .views import farmer_dashboard_view, customer_dashboard_view

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('verify-otp/', verify_otp_view, name='verify-otp'),
    path('redirect/', role_based_redirect, name='role-redirect'),

    path('farmer/login/', FarmerLoginView.as_view(), name='farmer-login'),
    path('customer/login/', CustomerLoginView.as_view(), name='customer-login'),
path('logout/', LogoutView.as_view(next_page=reverse_lazy('farmer-login')), name='logout'),

    path('farmer/dashboard/', farmer_dashboard_view, name='farmer-dashboard'),
    path('customer/dashboard/', customer_dashboard_view, name='customer-dashboard'),
]
