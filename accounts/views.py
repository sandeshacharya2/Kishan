from django.http import HttpResponse
from django.contrib.auth import get_user_model

def init_railway_admin(request):
    User = get_user_model()
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser("admin", "admin@kishan.com", "KishanSecure2025!")
        return HttpResponse("✅ Superuser created!")
    return HttpResponse("⚠️ Already exists.")