from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
from django.db.models.signals import post_save
from django.utils.translation import gettext as _
from django.dispatch import receiver


class EmailOTP(models.Model):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.created_at = timezone.now()
        self.save()

    def is_valid(self):
        return self.otp and (timezone.now() - self.created_at) <= timedelta(minutes=3)

    def __str__(self):
        return f"{self.email} - {self.otp}"

    @staticmethod
    def cleanup_expired():
        expiry_time = timezone.now() - timedelta(minutes=3)
        EmailOTP.objects.filter(created_at__lt=expiry_time).delete()


class Profile(models.Model):
    ROLE_CHOICES = (
        ('farmer', 'Farmer'),
        ('customer', 'Customer'),
        ('admin', 'Admin')
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='admin')
    address = models.CharField(max_length=255, default="Beni Municipality", editable=False)
    phonenumber = models.CharField(max_length=20)
    ward = models.CharField(max_length=100, blank=True, null=True)
    tole = models.CharField(max_length=100)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"


# Farmer specific profile
class FarmerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='farmer_profiles/', blank=True, null=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.user.username


# Customer specific profile (नयाँ थपिएको)
class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='customer_profiles/', blank=True, null=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    # थप fields चाहियो भने यहाँ थप्न सक्नुहुन्छ
    

    def __str__(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.user.username


# Signal to create or update profiles automatically
@receiver(post_save, sender=User)
def create_or_update_user_profiles(sender, instance, created, **kwargs):
    if created:
        # General Profile बनाउने
        Profile.objects.create(user=instance)

        # Role अनुसार specific profile बनाउने
        if hasattr(instance, 'profile') and instance.profile.role == 'farmer':
            FarmerProfile.objects.create(user=instance)
        elif hasattr(instance, 'profile') and instance.profile.role == 'customer':
            CustomerProfile.objects.create(user=instance)

    else:
        # General Profile update/बनाउने
        try:
            instance.profile.save()
        except Profile.DoesNotExist:
            Profile.objects.create(user=instance)

        # FarmerProfile update/बनाउने (role 'farmer' हो भने मात्र)
        if instance.profile.role == 'farmer':
            try:
                instance.farmerprofile.save()
            except FarmerProfile.DoesNotExist:
                FarmerProfile.objects.create(user=instance)

        # CustomerProfile update/बनाउने (role 'customer' हो भने मात्र)
        elif instance.profile.role == 'customer':
            try:
                instance.customerprofile.save()
            except CustomerProfile.DoesNotExist:
                CustomerProfile.objects.create(user=instance)
