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

class MusicalEntity(models.Model):
    mbid = models.CharField(max_length=64, null=True, blank=True)

    def __init__(self, *args, **kwargs):
        self.tags = []
        self.similar = []
        self.images = {}
        self.tracks = []
        self.events = []
        self.matches = []
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
            'autocorrect': 1,
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

    def lastfm_get_info(self, tree=None):
        if not tree:
            tree = self.lastfm_get_tree(self.get_type() + '.getInfo')
            if tree:
                tree = tree.find(self.get_type())
        
        if not tree:
            return None

        self.name = tree.find('name').text
        for element in tree.findall('image'):
            self.images[element.attrib['size']] = element.text
       
        # lastfm api is inconsistent, tags/tag/name is ok for artist.getInfo
        for element in tree.findall('tags/tag/name'):
            self.tags.append(element.text)
        # lastfm api is inconsistent, toptags/tag/name is ok for track.getInfo
        for element in tree.findall('toptags/tag/name'):
            self.tags.append(element.text)

        return tree

    def lastfm_search(self):
        klass = self.__class__
        tree = self.lastfm_get_tree(self.get_type() + '.search')

        for element in tree.findall('results/%smatches/%s' % (self.get_type(), self.get_type() )):
            match = klass(name=element.find('name').text)
            match.lastfm_get_info(element)
            self.matches.append(match)

class Artist(MusicalEntity):
    name = models.CharField(max_length=255, verbose_name=_(u'name'), unique=True, blank=False)

    def get_type(self):
        return 'artist'

    def youtube_get_term(self):
        return self.name

    def lastfm_get_info(self, tree=None):
        tree = super(Artist, self).lastfm_get_info(tree)
        
        self.description = getattr(tree.find('bio/summary'), 'text', None)

        for element in tree.findall('similar/artist'):
            similar = Artist()
            similar.lastfm_get_info(element)
            self.similar.append(similar)

    def lastfm_get_tracks(self, count=99):
        tree = self.lastfm_get_tree('artist.getTopTracks')
        for element in tree.findall('toptracks/track'):
            track = Track(name=element.find('name').text, artist=self)
            track.lastfm_get_info(element)
            self.tracks.append(track)

            count -= 1
            
            if not count:
                return True

    def lastfm_get_similar(self):
        tree = self.lastfm_get_tree('artist.getSimilar')
        for element in tree.findall('similarartists/artist'):
            artist = Artist(name=element.find('name').text)
            artist.lastfm_get_info(element)
            self.similar.append(artist)

    def lastfm_get_events(self):
        tree = self.lastfm_get_tree('artist.getEvents')
        event = None
        for element in tree.findall('events/event'):
            name = element.find('venue/name').text
            if event and event.name == name:
                continue
            event = Event(artist=self, name=name)
            event.lastfm_get_info(element)
            self.events.append(event)

class Event(MusicalEntity):
    artist = models.ForeignKey(Artist, verbose_name=_(u'artist'))
    name = models.CharField(max_length=255, verbose_name=_(u'name'), unique=True, blank=False)

    def lastfm_get_info(self, tree=None):
        if not tree:
            tree = self.lastfm_get_tree(self.get_type() + '.getInfo').find(self.get_type())
        
        self.name = tree.find('venue/name').text
        for element in tree.findall('image'):
            self.images[element.attrib['size']] = element.text

    def get_type(self):
        return 'event'

class Album(MusicalEntity):
    artist = models.ForeignKey(Artist, verbose_name=_(u'artist'))
    name = models.CharField(max_length=255, verbose_name=_(u'name'), unique=True, blank=False)
    
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
    artist = models.ForeignKey(Artist, verbose_name=_(u'artist'))
    album = models.ForeignKey(Album, verbose_name=_(u'album'), null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_(u'name'), unique=False)

    play_counter = models.IntegerField(verbose_name=_(u'played'), default=0)
    youtube_id = models.CharField(max_length=11)
    youtube_bugs = models.IntegerField(default=0)

    def lastfm_get_info(self, tree=None):
        tree = super(Track, self).lastfm_get_info(tree)
        self.description = getattr(tree.find('wiki/summary'), 'text', None)

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

    def lastfm_search(self):
        klass = self.__class__
        tree = self.lastfm_get_tree(self.get_type() + '.search')

        for element in tree.findall('results/%smatches/%s' % (self.get_type(), self.get_type() )):
            match = klass(name=element.find('name').text, 
                artist=Artist(name=element.find('artist').text))
            match.lastfm_get_info(element)
            self.matches.append(match)

#signals.pre_save.connect(resync, sender=Track)
#signals.pre_save.connect(resync, sender=Artist)
#signals.pre_save.connect(resync, sender=Album)
