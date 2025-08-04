from django.db import models
from django.contrib.auth.models import User
from products.models import Product

class ChatRoom(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='farmer_chats')
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_chats')
    farmer_accepted = models.BooleanField(default=False)
    farmer_rejected = models.BooleanField(default=False)

    def __str__(self):
        try:
            product_name = self.product.name
        except Product.DoesNotExist:
            product_name = "Deleted Product"

        result = f"Chat between {self.customer.username} and {self.farmer.username} for {product_name}"
        print(f"[DEBUG] __str__ called: {result}")
        return result

class Message(models.Model):
    chatroom = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bid_quantity = models.PositiveIntegerField(null=True, blank=True)
    is_bid = models.BooleanField(default=False)
    bid_status = models.CharField(
        max_length=10,
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected'),
        ],
        default='pending',
        null=True,
        blank=True
    )

    def __str__(self):
        result = f"Message by {self.sender.username} in {self.chatroom}"
        print(f"[DEBUG] Message __str__ called: {result}")
        return result
