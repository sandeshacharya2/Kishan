from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class RoleBasedBackend(ModelBackend):
    """
    Custom auth backend that checks username/password
    AND verifies that the user role matches the login page role.
    Also enforces case-sensitive username.
    """

    def authenticate(self, request, username=None, password=None, role=None, **kwargs):
        if not username or not password or not role:
            return None
        try:
            # Case-sensitive username check
            user = User.objects.get(username__exact=username)
            if user.check_password(password) and hasattr(user, 'profile') and user.profile.role == role:
                return user
        except User.DoesNotExist:
            return None
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
