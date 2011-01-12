from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from models import GfcProfile

class Auth(object):
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class GfcAuth(Auth):
    def authenticate(self, uid=None):
        try:
            return GfcProfile.objects.get(
                uid=uid,
                site=Site.objects.get_current()
            ).user
        except GfcProfile.DoesNotExist:
            return None
