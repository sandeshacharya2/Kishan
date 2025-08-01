# STEP 1: Create the model in products/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
class Product(models.Model):
    CATEGORY_CHOICES = [
        ('तरकारी', 'तरकारी'),
        ('फलफुल', 'फलफुल'),
        ('खाद्यान्न', 'खाद्यान्न'),
    ]
    UNIT_CHOICES = [
        ('किलो', 'किलो'),
        ('क्विन्टल', 'क्विन्टल'),
        ('दर्जन', 'दर्जन'),
        ('मुरी', 'मुरी'),
    ]

    farmer = models.ForeignKey(User, on_delete=models.CASCADE)
    main_category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    sub_category = models.CharField(max_length=100)
<<<<<<< HEAD
=======
    sub_category_roman = models.CharField(max_length=100, blank=True, null=True)

>>>>>>> sandesh
    quantity = models.FloatField()
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    price = models.FloatField(help_text="Price per unit")
    date_posted = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    def total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f"{self.sub_category} - {self.quantity} {self.unit}"
