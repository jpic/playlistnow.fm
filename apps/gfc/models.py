from django.db import models

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

class GfcProfile(models.Model):
    user = models.ForeignKey(User)
    site = models.ForeignKey(Site, default=Site.objects.get_current)
    uid = models.CharField(max_length=255, blank=False, null=False)
    url = models.TextField(null=True, blank=True)
    nick = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        if self.pk:
            user = self.user
        else:
            user = u'<no-user>'
        return u'%s: %s' % (user, self.uid)

    def authenticate(self):
        return authenticate(uid=self.uid)
