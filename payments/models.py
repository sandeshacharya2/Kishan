from django.db import models
from django.contrib.auth.models import User
from products.models import Product  

DELIVERY_CHOICES = [
    ('Pending', 'Pending'),
    ('Dispatched', 'Dispatched'),
    ('Delivered', 'Delivered'),
    ('Completed', 'Completed'),   # after customer confirms
    ('Dispute', 'Dispute'),       # if customer raises issue
]

PAYMENT_METHOD_CHOICES = [
    ('Esewa', 'eSewa'),
    ('COD', 'Cash on Delivery'),
]

PAYMENT_STATUS_CHOICES = [
    ('Pending', 'Pending'),       # initial COD state
    ('Pay', 'Pay Now'),           # after customer confirms delivery
    ('Waiting', 'Waiting Farmer Confirmation'),  # after customer clicks "Pay Now"
    ('Success', 'Success'),       # final
    ('Failed', 'Failed'),
]


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    # Common fields
    amount = models.FloatField()
    quantity = models.FloatField()

    # Payment info
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        default='Esewa'
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='Pending'
    )

    # For eSewa only
    pid = models.CharField(max_length=100, blank=True, null=True)  # Payment ID
    rid = models.CharField(max_length=100, blank=True, null=True)  # Reference ID

    # Delivery info
    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_CHOICES,
        default='Pending'
    )

    admin_notified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.product.sub_category} - {self.payment_method} - {self.payment_status}'
