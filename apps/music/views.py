import urllib2
import math

from django import http
from django import shortcuts
from django import template
from django.db.models import get_model
from django.template import defaultfilters
from django.contrib.auth import decorators
from django.conf import settings
from django.utils import simplejson

import gdata.youtube
import gdata.youtube.service

from models import *
#from forms import *

def return_json(data=None):
    if not data: 
        data = '[]'
    else: 
        data = simplejson.dumps(data)

    return http.HttpResponse(
        data,
        content_type='text/plain; charset=utf-8',
        mimetype='application/json'
    )

def music_artist_details(request, name, tab='overview', paginate_by=10,
    template_name='music/artist_details.html', extra_context=None):
    context = {
        'tab': tab,
    }

    name = name.replace('-', ' ')
    context['object'] = Artist(name=name)
    context['object'].lastfm_get_info()

    if tab == 'music':
        context['object'].lastfm_get_tracks()

        page = int(request.GET.get('page', 1))
        context['tracks'] = context['object'].tracks[(page-1)*paginate_by:(page-1)*paginate_by+paginate_by]
        context['totalPages'] = int(math.ceil(len(context['object'].tracks) / paginate_by))
        context['allPages'] = range(1, context['totalPages'] + 1)
        context['currentPage'] = page
    elif tab == 'similar':
        context['object'].lastfm_get_similar()
    elif tab == 'events':
        context['object'].lastfm_get_events()
    elif tab == 'overview':
        context['object'].lastfm_get_tracks()
        context['object'].tracks = context['object'].tracks[0:5]

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def music_album_details(request, name,
                  template_name='music/album_details.html', extra_context=None):
    context = {}

    context['object'] = Album(name=name)

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def music_track_details(request, name, artist, album=None,
    template_name='music/track_details.html', extra_context=None):
    context = {}

    name = name.replace('-', ' ')
    artist = artist.replace('-', ' ')

    context['object'] = Track(name=name)
    context['object'].artist = Artist(name=artist)
    context['object'].lastfm_get_info()
    context['object'].lastfm_get_similar()
    context['object'].similar = context['object'].similar[:5]

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def music_search_autocomplete(request, qname='term'):
    if not qname in request.GET:
        return return_json()

    if not request.GET[qname]:
        return return_json()

    url = 'http://www.last.fm/search/autocomplete?q=%s&force=1' % urllib2.quote(request.GET[qname].encode('utf-8'))
    try:
        upstream_response = urllib2.urlopen(url)
        upstream_response = simplejson.loads(upstream_response.read())
    except:
        return return_json()

    id = 1
    response = []
    for doc in upstream_response['response']['docs']:
        doc = dict(**doc)

        if 'track' in doc:
            doc['text'] = doc['track']

            if 'album' in doc and 'artist' in doc:
                doc['extra'] = "%s / %s" % (doc['album'], doc['artist'])
            elif 'artist' in doc:
                doc['extra'] = doc['artist']

            if 'artist' in doc:
                doc['url'] = urlresolvers.reverse('music_track_details', args=(
                    defaultfilters.slugify(doc['artist']),
                    defaultfilters.slugify(doc['track']),
                ))
            else:
                continue

            doc['image'] = 'http://ws.audioscrobbler.com/2.0/?api_key=%s&amp;track=%s&amp;method=track.getImageRedirect&amp;size=smallsquare' % (
                doc['track'],
                settings.LASTFM_API_KEY
            )

        elif 'album' in doc:
            doc['text'] = doc['album']
            doc['extra'] = doc['artist']

            doc['image'] = 'http://ws.audioscrobbler.com/2.0/?api_key=%s&amp;album=%s&amp;method=album.getImageRedirect&amp;size=smallsquare' % (
                doc['album'],
                settings.LASTFM_API_KEY
            )
            doc['url'] = urlresolvers.reverse('music_artist_details', args=(
                defaultfilters.slugify(doc['artist'])
            ,))

        elif 'artist' in doc:
            doc['text'] = doc['artist']
            doc['image'] = 'http://ws.audioscrobbler.com/2.0/?api_key=%s&amp;artist=%s&amp;method=artist.getImageRedirect&amp;size=smallsquare' % (
                doc['artist'],
                settings.LASTFM_API_KEY
            )
            doc['url'] = urlresolvers.reverse('music_artist_details', args=(
                defaultfilters.slugify(doc['artist'])
            ,))
        else:
            continue

        doc['id'] = id
        doc['image'] = 'http://userserve-ak.last.fm/serve/34s/%s.jpg' % doc['resid']

        response.append(doc)
        id += 1

    return return_json(response)

def music_search(request, qname='term',
    template_name='music/search.html', extra_context=None):
    context = {}

    if qname in request.GET.keys():
        q = request.GET[qname]
        
        try:
            if int(request.GET.get('search_artists', True)):
                artist = Artist(name=q)
                artist.lastfm_search()
                context['artists'] = artist.matches
        except lxml.etree.XMLSyntaxError: # some utf8 char failed
            pass

        try:
            if request.GET.get('search_tracks', True):
                track = Track(name=q)
                track.lastfm_search()
                context['tracks'] = track.matches
        except lxml.etree.XMLSyntaxError: # some utf8 char failed
            pass


    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))
