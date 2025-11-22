from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import farmer_dashboard_view

urlpatterns = [
    path('dashboard/', farmer_dashboard_view, name='farmer-dashboard'),
    path('add/', views.add_product, name='add-product'),
    path('edit/<int:product_id>/', views.edit_product, name='edit-product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete-product'),
    path('project/', views.project, name='project'),
    path('service/', views.service, name='service'),
    path('careers/', views.carrers, name='careers'),



    # path('marketplace/', views.marketplace_view, name='marketplace'),
    #  path('', views.landing_view, name='landing'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)