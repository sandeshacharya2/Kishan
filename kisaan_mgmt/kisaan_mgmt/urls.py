from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from accounts import views  # views import गरियो

from accounts.views import signup_view, landing_page, about, contact  # Import your views

urlpatterns = [
    path('', landing_page, name='landing'),   # Main landing page at "/"
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/farmer_login.html'), name='login'),

    # Login paths
    path('farmer/login/', auth_views.LoginView.as_view(template_name='accounts/farmer_login.html'), name='farmer-login'),
    path('customer/login/', auth_views.LoginView.as_view(template_name='accounts/customer_login.html'), name='customer-login'),

    path('switch-to-farmer/', views.switch_to_farmer, name='switch_to_farmer'),
    path('switch-to-customer/', views.switch_to_customer, name='switch_to_customer'),

    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'),
    path('signup/', signup_view, name='signup'),

    # Password reset paths
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),

    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
