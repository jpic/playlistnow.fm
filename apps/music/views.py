import urllib2
from urllib import urlencode
import math
import datetime
from lxml.html import fromstring

from django import http
from django import shortcuts
from django import template
from django.db.models import get_model
from django.db.models import Q
from django.template import defaultfilters
from django.contrib.auth import decorators
from django.conf import settings
from django.utils import simplejson
from django.contrib import messages
from socialregistration.utils import OAuthTwitter, get_token_prefix

from actstream import action

from models import *
from playlist.models import *
from forms import *

def shorten_url(url):
    data = urlencode((('long', url),))
    response = urllib2.urlopen('http://gw.gd/api.php', data)
    if response.getcode() != 200:
        return url
    return response.read()

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

def music_recommendation_thank(request, id):
    if not request.user.is_authenticated():
        return http.HttpResponseForbidden()

    try:
        r = Recommendation.objects.get(pk=id)
    except Recommendation.DoesNotExist:
        return http.HttpResponseForbidden()
    
    r.thanks = True
    r.thank_date = datetime.now()
    r.save()
            
    action.send(request.user, verb='thanks recommendation', action_object=r)

    return http.HttpResponse('you thanked')

def music_recommendation_add(request, form_class=RecommendationForm,
    template_name='music/recommendation_add.html', extra_context=None):

    if not request.user.is_authenticated():
        return http.HttpResponseForbidden('please authenticate')

    context = {
        'track_name': request.REQUEST.get('track_name', ''),
        'artist_name': request.REQUEST.get('artist_name', ''),
        'target_pk_list': request.REQUEST.get('target_pk_list', ''),
        'track': None,
        'friend_pk': request.REQUEST.get('user_pk', ''),
    }

    context['track'] = get_or_fake_track(context['track_name'], context['artist_name'])

    if request.method == 'POST' and context['track']:
        if request.GET.get('method', False) == 'facebook':
            request.facebook.graph.put_wall_post(request.POST.get('message'))
            msg = 'thanks for sharing <a href="%s">%s</a> on Facebook' % (
                context['track'].get_absolute_url(),
                unicode(context['track']),
            )
            return http.HttpResponse(msg)
        elif request.GET.get('method', False) == 'twitter':
            session_key = 'oauth_%s_access_token' % get_token_prefix(settings.TWITTER_REQUEST_TOKEN_URL)
            if session_key in request.session.keys():
                restore = request.session[session_key]
            else:
                restore = None

            for twitterprofile in request.user.twitterprofile_set.all():
                request.session[session_key] = {
                    'oauth_token_secret': 'krEu2rA0BbTyLmCfTQtHfv34wrFE6qVmLGRB9YR5es4', 
                    'oauth_token': twitterprofile.access_token, 
                    'user_id': twitterprofile.user_id,
                    'screen_name': twitterprofile.nick,
                }
                client = OAuthTwitter(
                    request, settings.TWITTER_CONSUMER_KEY,
                    settings.TWITTER_CONSUMER_SECRET_KEY,
                    settings.TWITTER_REQUEST_TOKEN_URL,
                )
                client.query('http://api.twitter.com/1/statuses/update.json', 'POST', {'status': request.POST.get('message')})
            
            if restore:
                request.session[session_key] = restore
            else:
                del request.session[session_key]

            msg = 'thanks for sharing <a href="%s">%s</a> on Twitter' % (
                context['track'].get_absolute_url(),
                unicode(context['track']),
            )
            return http.HttpResponse(msg)
        else:
            form = form_class(request.POST, instance=Recommendation(source=request.user, track=context['track']))
            if form.is_valid():
                save_if_fake_track(context['track'])
                recommendation = form.save()
                action.send(request.user, verb='recommends', action_object=recommendation)
                msg = 'thanks for recommending <a href="%s">%s</a> to <a href="%s">%s</a>' % (
                    recommendation.track.get_absolute_url(),
                    unicode(recommendation.track),
                    recommendation.target.playlistprofile.get_absolute_url(),
                    unicode(recommendation.target),
                )
                return http.HttpResponse(msg)
            else:
                print form.errors
    else:
        form = form_class()

    base = 'http://%s' % request.META.get('HTTP_HOST', 'http://pln.yourlabs.org')
    profiles = request.user.twitterprofile_set.all()
    if profiles:
        context['twitterprofile'] = profiles[0]
        context['twitterurl'] = shorten_url(base+context['track'].get_absolute_url())
    profiles = request.user.facebookprofile_set.all()
    if profiles:
        context['facebookprofile'] = profiles[0]
        context['facebookurl'] = base+context['track'].get_absolute_url()

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))


def music_badvideo(request):
    bad_youtube_id = request.POST.get('youtube_id', False)
    if not bad_youtube_id:
        return http.HttpResponseForbidden()

    new_id = ''
    bad_track_pk = request.POST.get('track_pk', '')
    bad_track_name = request.POST.get('track_name', '')
    bad_artist_name = request.POST.get('artist_name', '')

    if not bad_track_pk:
        t = Track(name=bad_track_name)
        t.artist = Artist(name=bad_artist_name)
        t.youtube_cache_reset()
    else:
        t = Track.objects.get(pk=bad_track_pk)
    t.youtube_cache_reset()

    for e in t.youtube_entries:
        m = re.match(r'.*/([0-9A-Za-z_-]*)/?$', e.id.text)
        if m and m.group(1) != bad_youtube_id:
            new_id = m.group(1)
            break

    if new_id:
        Track.objects.filter(youtube_id=bad_youtube_id).update(
            youtube_id=new_id)

    return http.HttpResponse(new_id)

def music_artist_fanship(request):
    if not request.method == 'POST':
        return http.HttpResponseForbidden()

    if not request.user.is_authenticated():
        return http.HttpResponseForbidden()

    if request.POST.get('artist_pk', False):
        artist = Artist.objects.get(pk=request.POST['artist_pk'])
        if not artist.image_medium:
            artist.lastfm_get_info()
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
