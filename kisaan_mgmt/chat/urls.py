from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('start/<int:product_id>/', views.start_chat, name='start_chat'),
    path('room/<int:chatroom_id>/', views.chatroom_detail, name='chatroom_detail'),
    path('accept/<int:chatroom_id>/', views.accept_chat, name='accept_chat'),
    path('reject/<int:chatroom_id>/', views.reject_chat, name='reject_chat'),
    path('accept_bid/<int:message_id>/', views.accept_bid, name='accept_bid'),
    
]
