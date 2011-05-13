import re
import logging
import htmlentitydefs
import urllib
import datetime
from lxml import etree

from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext as _
from django.core import urlresolvers
from django.template import defaultfilters
from django.conf import settings
from django.core.cache import cache

import gdata.youtube
import gdata.youtube.service

logger = logging.getLogger(__name__)
# Prevent: XMLSyntaxError: Attempt to load network entity
etree.set_default_parser(etree.XMLParser(no_network=False, recover=True))

def youtube_entry_generator(entries, exclude=''):
    OK = (
        'Syndication of this video was restricted by its owner.',
    )

    for entry in entries:
        m = re.match(r'.*/([0-9A-Za-z_-]*)/?$', entry.id.text)
        if not m:
            continue
        if not m.group(1):
            continue
        if m.group(1) in exclude:
            continue
        yield entry
        #try:
            #id = m.group(1)
            #t = etree.parse('http://gdata.youtube.com/feeds/api/videos/%s' % id)
            #r = t.xpath('.//yt:state', namespaces={'yt':'http://gdata.youtube.com/schemas/2007'})
            #restricted = False
            #for i in r:
                #if 'restricted' in i.text and i.text not in OK:
                    #restricted = True
            #if restricted:
                #continue
        #except:
            #continue

        #yield entry

def get_info_if_no_image(sender, instance, **kwargs):
    if not isinstance(instance, Artist):
        return None
    
    if not instance.name:
        return None

    if not instance.image_medium:
        instance.lastfm_get_info()
signals.pre_save.connect(get_info_if_no_image)

def save_if_fake_track(track):
    if not track.artist.pk:
        try:
            track.artist = Artist.objects.get(name=track.artist.name)
        except Artist.DoesNotExist:
            track.artist.save()
            # set track.artist_id
            track.artist = track.artist

    if not track.pk:
        try:
            track = Track.objects.get(artist=track.artist, name=track.name)
        except Track.DoesNotExist:
            track.save()

    return track

def get_or_create_track(track_name, artist_name=None):
    track = get_or_fake_track(track_name, artist_name)
    save_if_fake_track(track)
    return track

def get_or_fake_track(track_name, artist_name=None):
    artist = None
    if artist_name:
        try:
            artist = Artist.objects.get(name__iexact=artist_name)
        except Artist.DoesNotExist:
            artist = Artist(name=artist_name)
            artist.lastfm_get_info()

        try:
            track = Track.objects.get(name__iexact=track_name,
                artist__name__iexact=artist_name)
        except Track.DoesNotExist:
            track = Track(name=track_name, artist=artist)
            track.lastfm_get_info()
    else:
        try:
            track = Track.objects.get(name__iexact=track_name)
        except Track.DoesNotExist:
            track = Track(name=track_name)
    return track

class Recommendation(models.Model):
    source = models.ForeignKey('auth.User', related_name='recommends')
    target = models.ForeignKey('auth.User', related_name='recommendations')
    track  = models.ForeignKey('music.Track')
    thanks = models.BooleanField(default=False)
    message = models.TextField(null=True, blank=True)

    creation_date = models.DateTimeField(auto_now_add=True)
    thank_date = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        if self.thanks:
            and_was_thanked = 'and was thanked'
        else:
            and_was_thanked = ''

        return u'%s recommends %s to %s%s' % (
            self.source,
            self.track,
            self.target,
            and_was_thanked
        )

class MusicalEntity(models.Model):
    mbid = models.CharField(max_length=64, null=True, blank=True)
    image_small = models.CharField(max_length=100, null=True, blank=True)
    image_medium = models.CharField(max_length=100, null=True, blank=True)
    image_large =  models.CharField(max_length=100, null=True, blank=True)

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

    def to_dict(self):
        return {
            'name': self.name,
            'url': self.get_absolute_url(),
            'pk': self.pk or 0,
        }

    def get_absolute_url(self):
        slug = defaultfilters.slugify(self.name.replace('&', 'and'))
        if not len(slug):
            slug = urllib.quote(self.name.encode('utf-8'))
        return urlresolvers.reverse('music_%s_details' % self.get_type(), 
            args=(slug,))

    def __unicode__(self):
        return self.name

    def youtube_cache_reset(self):
        term = self.youtube_get_term()
        key = defaultfilters.slugify('youtube_entries for ' + term)
        if len(key) <= 250: # MemcachedKeyLengthError: Key length is > 250
            cache.delete(key)

    def youtube_ids(self, bad_ids=''):
        for entry in youtube_entry_generator(self.youtube_entries, bad_ids):
            m = re.match(r'.*/([0-9A-Za-z_-]*)/?$', entry.id.text)
            yield m.group(1)

    @property
    def youtube_entries(self):
        term = self.youtube_get_term()
        key = defaultfilters.slugify('youtube_entries for ' + term)

        if len(key) <= 250: # MemcachedKeyLengthError: Key length is > 250
            entry = cache.get(key)
        else:
            entry = None

        # crap results demonstrated: http://gdata.youtube.com/demo/index.html
        if entry and len(entry):
            return entry

        client = gdata.youtube.service.YouTubeService()
        query = gdata.youtube.service.YouTubeVideoQuery()
        
        query.vq = term.encode('utf-8')
        query.max_results = 15
        query.start_index = 1
        query.racy = 'exclude'
        query.format = '5'
        query.orderby = 'relevance'
        #query.restriction = 'fr'
        feed = client.YouTubeQuery(query)

        if len(key) <= 250: # MemcachedKeyLengthError: Key length is > 250
            cache.set(key, feed.entry, 24*3600)

        return feed.entry

    def lastfm_get_tree(self, method, **kwargs):
        kwargs.update({
            'autocorrect': 1,
            self.get_type(): unicode(self).encode('utf-8'),
        })

        if hasattr(self, 'artist'):
            kwargs['artist'] = unicode(self.artist).encode('utf-8')
        if hasattr(self, 'album'):
            kwargs['album'] = unicode(self.album).encode('utf-8')

        url = 'http://ws.audioscrobbler.com/2.0/?api_key=%s&method=%s&%s' % (
            settings.LASTFM_API_KEY,
            method,
            urllib.urlencode(kwargs)
        )

        logger.info(url)

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
        
        if tree is None: return None

        self.name = tree.find('name').text
        self.mbid = getattr(tree.find('mbid'), 'text', None)
        for element in tree.findall('image'):
            self.images[element.attrib['size']] = element.text
       
            attr = 'image_' + element.attrib['size']
            if hasattr(self, attr):
                setattr(self, attr, element.text)

        # lastfm api is inconsistent, tags/tag/name is ok for artist.getInfo
        for element in tree.findall('tags/tag/name'):
            self.tags.append(element.text)
        # lastfm api is inconsistent, toptags/tag/name is ok for track.getInfo
        for element in tree.findall('toptags/tag/name'):
            self.tags.append(element.text)

        return tree

    def lastfm_search(self, page=1, limit=100):
        klass = self.__class__
        tree = self.lastfm_get_tree(self.get_type() + '.search', page=page, limit=limit)

        if tree is None: return None
        self.opensearch_total_results = int(tree.getroot().getchildren()[0].getchildren()[1].text)

        for element in tree.findall('results/%smatches/%s' % (self.get_type(), self.get_type() )):
            match = klass(name=element.find('name').text)
            match.lastfm_get_info(element)
            self.matches.append(match)

    def lastfm_get_similar(self):
        cls = self.__class__
        tree = self.lastfm_get_tree(self.get_type() + '.getSimilar', limit=12)

        if tree is None: return None

        self.similar = []
        for element in tree.findall('similar'+self.get_type()+'s/'+self.get_type()):
            similar = cls(name=element.find('name').text)
            similar.lastfm_get_info(element)
            self.similar.append(similar)

def update_fans(sender, instance, **kwargs):
    if kwargs['action'] != 'post_add':
        return None

    if sender.__name__ == 'PlaylistProfile_fanof_artists':
        instance.last_fan_datetime = datetime.datetime.now()
    else:
        return None
    
    instance.save()
signals.m2m_changed.connect(update_fans)

class Artist(MusicalEntity):
    name = models.CharField(max_length=255, verbose_name=_(u'name'), unique=True, blank=False)
    rank = models.IntegerField(verbose_name=_(u'rank'), null=True, blank=True)
    last_playlist = models.ForeignKey('playlist.Playlist', verbose_name=_(u'last playlist'), null=True, blank=True)
    last_fan_datetime = models.DateTimeField(null=True, blank=True)

    def get_type(self):
        return 'artist'

    def youtube_get_term(self):
        return self.name

    def lastfm_get_info(self, tree=None):
        tree = super(Artist, self).lastfm_get_info(tree)
        if not tree:
            return None
        
        self.description = getattr(tree.find('bio/summary'), 'text', None)

        for element in tree.findall('similar/artist'):
            similar = Artist()
            similar.lastfm_get_info(element)
            self.similar.append(similar)

    def lastfm_get_tracks(self):
        tree = self.lastfm_get_tree('artist.getTopTracks')
        if not tree:
            return None

        for element in tree.findall('toptracks/track'):
            track = Track(name=element.find('name').text, artist=self)
            track.lastfm_get_info(element)
            self.tracks.append(track)

    def lastfm_get_events(self):
        tree = self.lastfm_get_tree('artist.getEvents')
        if not tree:
            return None
        event = None
        for element in tree.findall('events/event'):
            name = element.find('venue/name').text
            if event and event.name == name:
                continue
            event = Event(artist=self, name=name)
            event.lastfm_get_info(element)
            self.events.append(event)

    def get_tab_absolute_url(self, tab):
        return urlresolvers.reverse('music_artist_details_tab', args=(
            defaultfilters.slugify(self.name.replace('&', 'and')),
            tab
        ))

    def get_fans_tab_absolute_url(self):
        return self.get_tab_absolute_url('fans')
    def get_overview_tab_absolute_url(self):
        return self.get_tab_absolute_url('overview')
    def get_music_tab_absolute_url(self):
        return self.get_tab_absolute_url('music')
    def get_similar_tab_absolute_url(self):
        return self.get_tab_absolute_url('similar')
    def get_events_tab_absolute_url(self):
        return self.get_tab_absolute_url('events')
    def get_playlists_tab_absolute_url(self):
        return self.get_tab_absolute_url('playlists')

class Event(MusicalEntity):
    artist = models.ForeignKey(Artist, verbose_name=_(u'artist'))
    name = models.CharField(max_length=255, verbose_name=_(u'name'), unique=True, blank=False)

    def lastfm_get_info(self, tree=None):
        if not tree:
            tree = self.lastfm_get_tree(self.get_type() + '.getInfo').find(self.get_type())
        
        self.name = tree.find('venue/name').text
        self.city = tree.find('venue/location/city').text
        self.country = tree.find('venue/location/country').text
        self.date = tree.find('startDate').text
        for element in tree.findall('image'):
            self.images[element.attrib['size']] = element.text

            attr = 'image_' + element.attrib['size']
            if hasattr(self, attr):
                setattr(self, attr, element.text)

    def get_type(self):
        return 'event'

class Album(MusicalEntity):
    artist = models.ForeignKey(Artist, verbose_name=_(u'artist'))
    name = models.CharField(max_length=255, verbose_name=_(u'name'), unique=True, blank=False)
    
    def get_type(self):
        return 'album'
   
    def youtube_get_term(self):
        try:
            return u'%s - %s' % (
                self.artist.name,
                self.name
            )
        except Artist.DoesNotExist:
            return self.name

    def lastfm_get_info(self):
        tree = self.lastfm_get_tree('album.getInfo')
        if not tree:
            return None
        self.name = tree.find('album/name').text
        for element in tree.findall('album/toptags/tag/name'):
            self.tags.append(element.text)
        for element in tree.findall('album/image'):
            self.images[element.attrib['size']] = element.text

            attr = 'image_' + element.attrib['size']
            if hasattr(self, attr):
                setattr(self, attr, element.text)

class Track(MusicalEntity):
    artist = models.ForeignKey(Artist, verbose_name=_(u'artist'))
    album = models.ForeignKey(Album, verbose_name=_(u'album'), null=True, blank=True)
    name = models.CharField(max_length=255, verbose_name=_(u'name'), unique=False)

    play_counter = models.IntegerField(verbose_name=_(u'played'), default=0)
    youtube_id = models.CharField(max_length=11, null=True, blank=True)
    youtube_bugs = models.IntegerField(default=0)

    class Meta:
        unique_together = (('artist', 'name'),)

    def to_dict(self, with_artist=True, with_youtube_best_id=True):
        data = {
            'name': self.name,
            'url': self.get_absolute_url(),
            'pk': self.pk or 0,
        }

        if with_artist:
            data['artist'] = self.artist.to_dict()
       
        if with_youtube_best_id:
            data['youtube_best_id'] = self.youtube_get_best()

        return data

    def youtube_get_best(self):
        if self.youtube_id:
            return self.youtube_id
        elif len(self.youtube_entries) > 0:
            m = re.match(r'.*/([0-9A-Za-z_-]*)/?$', self.youtube_entries[0].id.text)
            if m and m.group(1):
                Track.objects.filter(name__iexact=self.name, artist__name__iexact=self.artist.name).update(youtube_id=m.group(1))
                return m.group(1)
            else:
                print "failed to find youtube in", self.youtube_entries
                print "failed to find youtube in", self.youtube_entries[0]
                print "failed to find youtube in", self.youtube_entries[0].id
                print "failed to find youtube in", self.youtube_entries[0].id.text

    def lastfm_get_info(self, tree=None):
        tree = super(Track, self).lastfm_get_info(tree)

        if not tree:
            return None

        self.description = getattr(tree.find('wiki/summary'), 'text', None)
        try:
            self.artist
        except Artist.DoesNotExist:
            self.artist = Artist(name=tree.find('artist/name').text)

    def youtube_get_term(self):
        try:
            return u'%s - %s' % (
                self.artist.name,
                self.name
            )
        except Artist.DoesNotExist:
            return self.name
    
    def get_type(self):
        return 'track'

    def get_absolute_url(self):
        if isinstance(self.artist, Artist):
            artist = self.artist.name
        else:
            artist = self.artist
        
        artist = defaultfilters.slugify(artist.replace('&', 'and')) or urllib.quote(artist.replace('&', 'and').encode('utf-8'))
        name = defaultfilters.slugify(self.name.replace('&', 'and')) or urllib.quote(self.name.replace('&', 'and').encode('utf-8'))

        if not len(name):
            return urlresolvers.reverse('music_artist_details', args=(artist,))

        url = urlresolvers.reverse('music_track_details', args=(
            artist, name
        ))

        return url

    def lastfm_search(self, page=1, limit=100):
        klass = self.__class__
        tree = self.lastfm_get_tree(self.get_type() + '.search', page=page, limit=limit)
        
        if tree is None: return None

        self.opensearch_total_results = int(tree.getroot().getchildren()[0].getchildren()[1].text)

        for element in tree.findall('results/%smatches/%s' % (self.get_type(), self.get_type() )):
            match = klass(name=element.find('name').text, 
                artist=Artist(name=element.find('artist').text))
            match.lastfm_get_info(element)
            self.matches.append(match)
