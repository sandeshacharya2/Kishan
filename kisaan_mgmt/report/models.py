# reports/models.py
from accounts.models import FarmerProfile, CustomerProfile
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class FarmerReport(models.Model):
    """
    Model for reports submitted by farmers.
    """
    CATEGORY_CHOICES = [
        ('product_quality', 'Product Quality'),
        ('transaction_issue', 'Transaction Problem'),
        ('customer_behavior', 'Customer Behavior'),
        ('delivery_issue', 'Delivery Delay'),
        ('payment_issue', 'Payment Problem'),
        ('other', 'Other'),
    ]

    farmer = models.ForeignKey(FarmerProfile, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_solved = models.BooleanField(default=False)
    solved_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"[{'Solved' if self.is_solved else 'Pending'}] {self.subject} by {self.farmer.user.username}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Farmer Report"
        verbose_name_plural = "Farmer Reports"

class CustomerReport(models.Model):
    """
    Model for reports submitted by customers.
    """
    CATEGORY_CHOICES = [
        ('product_quality', 'Product Quality'),
        ('transaction_issue', 'Transaction Problem'),
        ('farmer_behavior', 'Farmer Behavior'),
        ('delivery_issue', 'Delivery Delay'),
        ('product_not_received', 'Product Not Received'),
        ('other', 'Other'),
    ]

    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    subject = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_solved = models.BooleanField(default=False)
    solved_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"[{'Solved' if self.is_solved else 'Pending'}] {self.subject} by {self.customer.user.username}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Customer Report"
        verbose_name_plural = "Customer Reports"