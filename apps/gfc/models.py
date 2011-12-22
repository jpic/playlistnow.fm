from django.db import models

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.sites.models import Site

class LaFacebookProfile(models.Model):
    user = models.ForeignKey(User)
    website = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    link = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    middle_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    hometown = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)

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
