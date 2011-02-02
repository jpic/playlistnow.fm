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
from django.contrib import messages

from actstream import action

from models import *
from playlist.models import *
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

def music_artist_fanship(request):
    if not request.method == 'POST':
        return http.HttpResponseForbidden()

    if not request.user.is_authenticated():
        return http.HttpResponseForbidden()

    if request.POST.get('artist_pk', False):
        artist = Artist.objects.get(pk=request.POST['artist_pk'])
    else:
        artist = Artist(name=request.POST.get('artist_name'))
        artist.lastfm_get_info()
        artist.save()
    
    if request.POST.get('action') == 'add':
        artist.fans.add(request.user.playlistprofile)
        action.send(request.user, verb='becomes fan of artist', action_object=artist)
        msg = 'thanks for becoming fan of <a href="%s">%s</a>' % (
            artist.get_absolute_url(),
            unicode(artist)
        )
        messages.add_message(request, messages.INFO, msg)

    else:
        artist.fans.remove(request.user.playlistprofile)
        #action.send(request.user, verb='is not anymore a fan of artist', action_object=artist)
        msg = 'thanks for quiting the fanclub of artist <a href="%s">%s</a>' % (
            artist.get_absolute_url(),
            unicode(artist)
        )
        messages.add_message(request, messages.INFO, msg)

    return http.HttpResponseRedirect(request.POST['next'])

def music_artist_details(request, name, tab='overview', paginate_by=10,
    template_name='music/artist_details.html', extra_context=None):
    context = {
        'tab': tab,
        'is_fan': False,
    }

    name = name.replace('-', ' ')
    context['object'] = Artist(name=name)
    context['object'].lastfm_get_info()
    try:
        context['object'].local_artist = Artist.objects.get(name__iexact=context['object'].name)

        context['playlists_including_artist'] = Playlist.objects.filter(tracks__artist=context['object'].local_artist).distinct('name')

        context['playlists_including_artist_slice'] = context['playlists_including_artist']._clone()[:3]
        context['artist_fans_slice'] = context['object'].local_artist.fans.all()[:20]

        if request.user.is_authenticated():
            context['is_fan'] = context['object'].local_artist.fans.filter(user__pk=request.user.pk).count()
    except Artist.DoesNotExist:
        pass

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

def music_search_autocomplete(request, qname='query'):
    if not request.GET.get(qname, False):
        return return_json()

    url = 'http://www.last.fm/search/autocomplete?q=%s&force=1' % urllib2.quote(request.GET[qname].encode('utf-8'))
    try:
        upstream_response = urllib2.urlopen(url)
        upstream_response = simplejson.loads(upstream_response.read())
        print upstream_response
    except:
        return return_json()

    response = {
        'query': request.GET[qname].encode('utf-8'),
        'suggestions': [],
        'data': [],
    }

    for doc in upstream_response['response']['docs']:
        if 'image' in doc.keys():
            doc['html'] = '<img src="http://userserve-ak.last.fm/serve/34s/%s" /> ' % doc['image']
        if 'track' in doc.keys():
            doc['url'] = urlresolvers.reverse('music_track_details', args=(
                defaultfilters.slugify(doc['artist']),
                defaultfilters.slugify(doc['track']),
            ))
            doc['html'] += '%s / %s' % (
                doc['track'],
                doc['artist']
            )
            suggestion = doc['track']
        elif 'album' in doc.keys():
            continue
        elif 'artist' in doc.keys():
            doc['url'] =  urlresolvers.reverse('music_artist_details', args=(
                defaultfilters.slugify(doc['artist']),
            ))
            doc['html'] += doc['artist']
            suggestion = doc['artist']
        else:
            continue

        response['suggestions'].append(suggestion)
        response['data'].append(doc)

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
