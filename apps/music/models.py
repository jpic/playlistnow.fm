import re
import htmlentitydefs
import urllib
from lxml import etree

from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext as _
from django.core import urlresolvers
from django.template import defaultfilters
from django.conf import settings

import gdata.youtube
import gdata.youtube.service

# Prevent: XMLSyntaxError: Attempt to load network entity
etree.set_default_parser(etree.XMLParser(no_network=False))

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

    def __init__(self, *args, **kwargs):
        self.tags = []
        self.similar = []
        self.images = {}
        super(MusicalEntity, self).__init__(*args, **kwargs)

    class Meta:
        abstract = True

    def get_absolute_url(self):
        return urlresolvers.reverse('music_%s_details' % self.get_type(), 
            args=(defaultfilters.slugify(self.name),))

    def __unicode__(self):
        return self.name

    @property
    def youtube_entries(self):
        client = gdata.youtube.service.YouTubeService()
        query = gdata.youtube.service.YouTubeVideoQuery()
        
        query.vq = self.youtube_get_term().encode('utf-8')
        query.max_results = 1
        query.start_index = 1
        query.racy = 'exclude'
        query.format = '5'
        query.orderby = 'relevance'
        #query.restriction = 'fr'
        feed = client.YouTubeQuery(query)
        
        return feed.entry

    def lastfm_get_tree(self, method):
        kwargs = {
            'autocorrect': 0,
            self.get_type(): unicode(self).encode('utf-8'),
        }

        if hasattr(self, 'artist'):
            kwargs['artist'] = unicode(self.artist).encode('utf-8')
        if hasattr(self, 'album'):
            kwargs['album'] = unicode(self.album).encode('utf-8')

        url = 'http://ws.audioscrobbler.com/2.0/?api_key=%s&method=%s&%s' % (
            settings.LASTFM_API_KEY,
            method,
            urllib.urlencode(kwargs)
        )
        print url

        try:
            tree = etree.parse(url)
            return tree
        except IOError:
            print "Did not work: "+url
            return None

class Artist(MusicalEntity):
    def get_type(self):
        return 'artist'

    def youtube_get_term(self):
        return self.name

    def lastfm_get_info(self, tree=None):
        if not tree:
            tree = self.lastfm_get_tree('artist.getInfo').find('artist')
        self.name = tree.find('name').text
        for element in tree.findall('tags/tag/name'):
            self.tags.append(element.text)
        for element in tree.findall('image'):
            self.images[element.attrib['size']] = element.text
        self.description = getattr(tree.find('bio/summary'), 'text', None)
        for element in tree.findall('similar/artist'):
            similar = Artist()
            similar.lastfm_get_info(element)
            self.similar.append(similar)

class Album(MusicalEntity):
    artist = models.ForeignKey(Artist, verbose_name=_(u'artist'))
    
    def get_type(self):
        return 'album'
   
    def youtube_get_term(self):
        return u'%s - %s' % (
            self.artist.name,
            self.name
        )

    def lastfm_get_info(self):
        tree = self.lastfm_get_tree('album.getInfo')
        self.name = tree.find('album/name').text
        for element in tree.findall('album/toptags/tag/name'):
            self.tags.append(element.text)
        for element in tree.findall('album/image'):
            self.images[element.attrib['size']] = element.text

class Track(MusicalEntity):
    album = models.ForeignKey(Album, verbose_name=_(u'album'))
    artist = models.ForeignKey(Artist, verbose_name=_(u'artist'))

    def lastfm_get_info(self):
        tree = self.lastfm_get_tree('track.getInfo')
        self.name = tree.find('track/name').text
        for element in tree.findall('track/toptags/tag/name'):
            self.tags.append(element.text)
        for element in tree.findall('track/image'):
            self.images[element.attrib['size']] = element.text
        self.description = tree.find('track/wiki/summary').text

    def youtube_get_term(self):
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
