from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
from django.db.models.signals import post_save
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


class Profile(models.Model):
    ROLE_CHOICES = (
        ('farmer', 'Farmer'),
        ('customer', 'Customer'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    address = models.CharField(max_length=255, default="Beni Municipality", editable=False)
    phonenumber = models.CharField(max_length=20)
    ward = models.CharField(max_length=100, blank=True, null=True)
    tole = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username} Profile"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        # Only create on user creation
        Profile.objects.create(user=instance)
    else:
        # Try saving profile, or create if missing
        try:
            instance.profile.save()
        except Profile.DoesNotExist:
            Profile.objects.create(user=instance)
