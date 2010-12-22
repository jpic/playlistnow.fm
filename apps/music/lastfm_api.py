import urllib
from lxml import etree

import lastfm

from django.conf import settings

from models import *

etree.set_default_parser(etree.XMLParser(no_network=False))

def lastfm_get_api():
    return lastfm.Api(settings.LASTFM_API_KEY)

def lastfm_get_tree(method, **kwargs):
    for k, v in kwargs.items():
        kwargs[k] = unicode(v).encode('utf-8')
    
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

def lastfm_get_info(entity, full=False):
    if not entity.name:
        return False

    kwargs = {}
    if isinstance(entity, Artist):
        kwargs['artist'] = entity.name
    elif isinstance(entity, Album):
        kwargs['artist'] = entity.artist.name
        kwargs['album'] = entity.name
    elif isinstance(entity, Track):
        kwargs['artist'] = entity.artist.name
        kwargs['track'] = entity.name

    tree = lastfm_get_tree(entity.get_type() + '.getInfo', **kwargs)
    in_similar = in_tag = False
    artist = False
    entity.name = None
    if hasattr(entity, 'artist'):
        entity.artist.name = None

    if not hasattr(entity, 'similar'):
         entity.similar = []

    for item in tree.iter():
        if item.tag == 'similar':
            in_similar = True
        elif item.tag == 'tag' or item.tag == 'toptags':
            in_similar = False
            in_tag = True
        elif item.tag == 'name' and in_tag:
            if not hasattr(entity, 'tags'):
                entity.tags = []
            entity.tags.append(item.text)
            in_tag = False

        elif in_similar:
            if item.tag == 'artist':
                if artist:
                     entity.similar.append(artist)
                
                artist = Artist()
            if item.tag == 'name':
                artist.name = item.text
            if item.tag == 'image':
                if item.attrib.get('size', False) == 'small':
                    artist.image_small = item.text
                if item.attrib.get('size', False) == 'medium':
                    artist.image_medium = item.text
                if item.attrib.get('size', False) == 'large':
                    artist.image_large = item.text
                if item.attrib.get('size', False) == 'mega':
                    artist.image_mega = item.text
        else:
            if item.tag == 'name' and not entity.name:
                entity.name = item.text
            elif hasattr(entity, 'artist') and item.tag == 'name' and not entity.artist.name:
                entity.artist.name = item.text
            elif item.tag == 'mbid':
                entity.mbid = item.text
            elif item.tag == 'url':
                entity.lastfm_url = item.text
            elif item.tag == 'image':
                if item.attrib.get('size', False) == 'small':
                    entity.image_small = item.text
                if item.attrib.get('size', False) == 'medium':
                    entity.image_medium = item.text
                if item.attrib.get('size', False) == 'large':
                    entity.image_large = item.text
                if item.attrib.get('size', False) == 'mega':
                    entity.image_mega = item.text
                entity.image_url = item.text
            elif item.tag == 'summary':
                entity.description = item.text
            #elif item.tag == 'name':
                #entity.name = item.text

    if isinstance(entity, Track):
        tree = lastfm_get_tree('track.getSimilar', **kwargs)
        similar_tracks = tree.getroot().getchildren()[0]

        track = None
        for similar_track in similar_tracks.getchildren():
            for item in similar_track.getchildren():
                if item.tag == 'name':
                    if track:
                        entity.similar.append(track)

                    track = Track(name=item.text)

                if item.tag == 'image':
                    if item.attrib.get('size', False) == 'small':
                        track.image_small = item.text
                    if item.attrib.get('size', False) == 'medium':
                        track.image_medium = item.text
                    if item.attrib.get('size', False) == 'large':
                        track.image_large = item.text
                    if item.attrib.get('size', False) == 'mega':
                        track.image_mega = item.text
                    track.image_url = item.text

                elif item.tag == 'artist':
                    for artist_item in item.getchildren():
                        if artist_item.tag == 'name':
                            track.artist = Artist(name=artist_item.text)

    elif isinstance(entity, Artist):
        tree = lastfm_get_tree('artist.getTopTracks', **kwargs)
        top_tracks = tree.getroot().getchildren()[0]

        if not hasattr(entity, 'top_tracks'):
            entity.top_tracks = []

        track = None
        for top_track in top_tracks.getchildren():
            for item in top_track.getchildren():
                if item.tag == 'name':
                    if track:
                        entity.top_tracks.append(track)

                    track = Track(name=item.text, artist=entity)

                if item.tag == 'image':
                    if item.attrib.get('size', False) == 'small':
                        track.image_small = item.text
                    if item.attrib.get('size', False) == 'medium':
                        track.image_medium = item.text
                    if item.attrib.get('size', False) == 'large':
                        track.image_large = item.text
                    if item.attrib.get('size', False) == 'mega':
                        track.image_mega = item.text
                    track.image_url = item.text

    return entity
