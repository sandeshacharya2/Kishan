from django.contrib import admin
from .models import Profile, FarmerProfile, CustomerProfile

admin.site.register(Profile)
admin.site.register(FarmerProfile)
admin.site.register(CustomerProfile)
