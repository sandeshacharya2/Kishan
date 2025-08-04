# models.py
from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField()
    farmer = models.ForeignKey(User, on_delete=models.CASCADE)

class ChatRoom(models.Model):
    farmer = models.ForeignKey(User, related_name='farmer_chats', on_delete=models.CASCADE)
    customer = models.ForeignKey(User, related_name='customer_chats', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bid_quantity = models.PositiveIntegerField(null=True, blank=True)
    is_bid = models.BooleanField(default=False)
    bid_status = models.CharField(max_length=10, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ], default='pending')
