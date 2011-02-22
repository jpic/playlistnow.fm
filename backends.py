from django.contrib.auth import backends
from django.contrib.auth.models import User

class ModelBackend(backends.ModelBackend):
    def authenticate(self, username=None, password=None):
        users = User.objects.filter(username=username).select_related()
        if len(users) > 0:
            user = users[0]
            if user.check_password(password):
                return user
        return None


