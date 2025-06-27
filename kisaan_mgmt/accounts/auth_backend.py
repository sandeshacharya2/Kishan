from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class RoleBasedBackend(ModelBackend):
    """
    Custom auth backend that checks username/password
    AND verifies user role matches login page role.
    """

    def authenticate(self, request, username=None, password=None, role=None, **kwargs):
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                if hasattr(user, 'profile') and user.profile.role == role:
                    return user
                # If roles don't match, authentication fails
                return None
        except User.DoesNotExist:
            return None
