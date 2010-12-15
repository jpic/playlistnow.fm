import urllib2

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

from lastfm_api import *
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

def music_artist_details(request, name,
    template_name='music/artist_details.html', extra_context=None):
    context = {}

    name = name.replace('-', ' ')
    context['object'] = Artist(name=name)
    lastfm_get_info(context['object'])
    context['object'].top_tracks = context['object'].top_tracks[:5]

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def music_album_details(request, name,
                  template_name='music/album_details.html', extra_context=None):
    context = {}

    context['object'] = Album(name=name)
    lastfm_get_info(context['object'])

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
    lastfm_get_info(context['object'])
    context['object'].similar = context['object'].similar[:5]

    client = gdata.youtube.service.YouTubeService()
    query = gdata.youtube.service.YouTubeVideoQuery()
    
    query.vq = "%s - %s" % (
        context['object'].artist.name,
        context['object'].name
    )
    query.max_results = 1
    query.start_index = 1
    query.racy = 'exclude'
    query.format = '5'
    query.orderby = 'relevance'
    #query.restriction = 'fr'
    feed = client.YouTubeQuery(query)
    
    context['object'].youtube = []
    for entry in feed.entry:
        context['object'].youtube.append(entry)
    context['object'].youtube = context['object'].youtube[:1]

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def music_find(request, qname='term'):
    if request.method != 'POST' or qname not in request.POST:
        return http.HttpResponseBadRequest()
 
    term = request.POST[qname]

    url = 'http://www.last.fm/search/autocomplete?q=%s&force=1' % urllib2.quote(term.encode('utf-8'))
    #try:
    upstream_response = urllib2.urlopen(url)
    upstream_response = simplejson.loads(upstream_response.read())
    doc = upstream_response['response']['docs'][0]

    if 'track' in doc:
        model_class = Track
    elif 'album' in doc:
        model_class = Album
    elif 'artist' in doc:
        model_class = Artist

    model, created = model_class.objects.get_or_create(name=term)

    if created:
        Lastfm().resync(model).save()

    url = model.get_absolute_url()
    #except:
        #url = request.META.get('HTTP_REFERER', '/')

    return http.HttpResponseRedirect(url)

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
            api = get_lastfm_api()
            artists = api.search_artist(q)
            
            context['artists'] = []
            for artist in artists:
                if not artist.streamable:
                    continue
                context['artists'].append(artist)
        except lastfm.LastfmError:
            pass

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))
