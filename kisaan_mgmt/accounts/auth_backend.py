from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class RoleBasedBackend(ModelBackend):
    """
    Custom auth backend that checks username/password
    AND verifies user role matches login page role.
    """

    def authenticate(self, request, username=None, password=None, role=None, **kwargs):
        if username is None or password is None or role is None:
            return None
        try:
            user = User.objects.get(username=username)
            if user.check_password(password) and hasattr(user, 'profile') and user.profile.role == role:
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
