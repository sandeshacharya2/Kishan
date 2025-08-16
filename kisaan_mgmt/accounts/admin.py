from django.contrib import admin
from .models import Profile, FarmerProfile, CustomerProfile, FarmerReview

admin.site.register(Profile)
admin.site.register(FarmerProfile)
admin.site.register(CustomerProfile)
admin.site.register(FarmerReview)
