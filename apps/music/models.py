import re, htmlentitydefs

from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext as _
from django.core import urlresolvers
from django.template import defaultfilters

import gdata.youtube
import gdata.youtube.service

##
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.

def unescape(text):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return re.sub("&#?\w+;", fixup, text)

def strip_tags(text): 
     finished = 0 
     while not finished: 
         finished = 1 
         start = text.find("<") 
         if start >= 0: 
             stop = text[start:].find(">") 
             if stop >= 0: 
                 text = text[:start] + text[start+stop+1:] 
                 finished = 0 
     return text

class MusicalEntity(models.Model):
    mbid = models.CharField(max_length=64, null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_(u'name'), unique=True, blank=False)

    class Meta:
        abstract = True

    def get_absolute_url(self):
        return urlresolvers.reverse('music_%s_details' % self.get_type(), 
            args=(defaultfilters.slugify(self.name),))

    def __unicode__(self):
        return self.name

    @property
    def youtube(self):
        if hasattr(self, '_youtube'):
            return self._youtube

        client = gdata.youtube.service.YouTubeService()
        query = gdata.youtube.service.YouTubeVideoQuery()
        
        query.vq = self.get_term()
        query.max_results = 1
        query.start_index = 1
        query.racy = 'exclude'
        query.format = '5'
        query.orderby = 'relevance'
        #query.restriction = 'fr'
        feed = client.YouTubeQuery(query)
        
        self._youtube = []
        for entry in feed.entry:
            self._youtube.append(entry)
        return self._youtube

class Artist(MusicalEntity):
    def get_type(self):
        return 'artist'

    def get_term(self):
        return self.name

class Album(MusicalEntity):
    artist = models.ForeignKey(Artist, verbose_name=_(u'artist'))
    
    def get_type(self):
        return 'album'
   
    def get_term(self):
        return u'%s - %s' % (
            self.artist.name,
            self.name
        )

class Track(MusicalEntity):
    album = models.ForeignKey(Album, verbose_name=_(u'album'))
    artist = models.ForeignKey(Artist, verbose_name=_(u'artist'))
    
    def get_term(self):
        return u'%s - %s' % (
            self.artist.name,
            self.name
        )

    def get_type(self):
        return 'track'

    def get_absolute_url(self):
        if isinstance(self.artist, Artist):
            artist = self.artist.name
        else:
            artist = self.artist

        artist = defaultfilters.slugify(artist)

        return urlresolvers.reverse('music_track_details', args=(
            artist, defaultfilters.slugify(self.name)
        ))

#signals.pre_save.connect(resync, sender=Track)
#signals.pre_save.connect(resync, sender=Artist)
#signals.pre_save.connect(resync, sender=Album)
