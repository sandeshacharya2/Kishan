from django.db import models
from django.contrib.auth.models import User
from products.models import Product  # Ensure this import works
DELIVERY_CHOICES = [
    ('Pending', 'Pending'),
    ('Dispatched', 'Dispatched'),
    ('Delivered', 'Delivered'),
    ('Completed', 'Completed'),   # after customer confirms
    ('Dispute', 'Dispute'),       # if customer raises issue
]


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    pid = models.CharField(max_length=100)  # Payment ID
    rid = models.CharField(max_length=100)  # Reference ID from eSewa
    amount = models.FloatField()
    quantity = models.FloatField()
    status = models.CharField(max_length=20)  # e.g., 'Success', 'Failure'
    admin_notified = models.BooleanField(default=False)

    delivery_status = models.CharField(
    max_length=20,
    choices=DELIVERY_CHOICES,
    default='Pending'
)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f'{self.user.username} - {self.product.sub_category} - {self.status}'
