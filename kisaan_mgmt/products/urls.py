from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('dashboard/', views.farmer_dashboard_view, name='farmer-dashboard'),
    path('add/', views.add_product, name='add-product'),
    path('edit/<int:product_id>/', views.edit_product, name='edit-product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete-product'),
    # path('marketplace/', views.marketplace_view, name='marketplace'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)