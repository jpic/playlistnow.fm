from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext as _
from django.core import urlresolvers

from tagging.models import Tag

class Artist(models.Model):
    name = models.CharField(max_length=100, verbose_name=_(u'name'))

class Album(models.Model):
    artist = models.ForeignKey(Artist, verbose_name=_(u'artist'))
    
    title = models.CharField(max_length=100, verbose_name=_(u'title'))

class Track(models.Model):
    album = models.ForeignKey(Album, verbose_name=_(u'album'))
    
    title = models.CharField(max_length=100, verbose_name=_(u'title'))
