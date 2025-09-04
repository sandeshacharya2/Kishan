from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class EmailBackend(ModelBackend):
    """
    Authenticate using email (strict case-sensitive) and password.
    Optional role check included.
    """
    def authenticate(self, request, username=None, password=None, role=None, **kwargs):
        if not username or not password:
            return None

        try:
            user = User.objects.get(email__iexact=username)  # DB may be case-insensitive
        except User.DoesNotExist:
            return None

        # Enforce strict case-sensitive email check in Python
        if user.email != username:
            return None

        # Optional role check
        if role and (not hasattr(user, "profile") or user.profile.role != role):
            return None

        # Password check
        if user.check_password(password):
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
