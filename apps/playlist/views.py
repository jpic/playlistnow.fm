import simplejson
import math

from django import http
from django import shortcuts
from django import template
from django.contrib import messages
from django.contrib.auth import decorators
from django.db.models import Q
from tagging.models import Tag
from actstream import action

from music.models import *
from models import *
from forms import *

def playlist_fanship(request, playlist_pk):
    if not request.method == 'POST':
        return http.HttpResponseForbidden()

    if not request.user.is_authenticated():
        return http.HttpResponseForbidden()

    if not 'action' in request.POST:
        return http.HttpResponseForbidden()

    playlist = Playlist.objects.get(pk=playlist_pk)
    
    if request.POST.get('action') == 'add':
        playlist.fans.add(request.user.playlistprofile)
        action.send(request.user, verb='bookmarks playlist', action_object=playlist)
        msg = 'thanks for bookmarking <a href="%s">%s</a>' % (
            playlist.get_absolute_url(),
            unicode(playlist)
        )
        messages.add_message(request, messages.INFO, msg)

    else:
        playlist.fans.remove(request.user.playlistprofile)
        #action.send(request.user, verb='is not anymore a fan of playlist', action_object=playlist)
        msg = 'thanks for removing playlist <a href="%s">%s</a> from bookmarks' % (
            playlist.get_absolute_url(),
            unicode(playlist)
        )
        messages.add_message(request, messages.INFO, msg)

    return http.HttpResponseRedirect(request.POST['next'])

@decorators.login_required
def playlist_track_modify(request,
    template_name='playlist/track_modify.html', extra_context=None):

    context = {
        'action': request.GET.get('action', request.POST.get('action', 'add')),
        'status': None,
        'playlist': {
                'pk': request.GET.get('playlist_pk', request.POST.get('playlist_pk', False)),
                'name': request.GET.get('playlist_name', request.POST.get('playlist_name', False)),
        },
        'track': {
            'artist': {
                'pk': request.GET.get('artist_pk', request.POST.get('artist_pk', False)),
                'name': request.GET.get('artist_name', request.POST.get('artist_name', False)),
            },
            'pk': request.GET.get('track_pk', request.POST.get('track_pk', False)),
            'name': request.GET.get('track_name', request.POST.get('track_name', False)),
        }
    }

    if context['playlist']['pk']:
        try:
            context['playlist'] = Playlist.objects.all_with_hidden().get(pk=context['playlist']['pk'])
        except Playlist.DoesNotExist:
            pass
    elif context['playlist']['name']:
        context['playlist'] = Playlist(
            creation_user=request.user,
            name=context['playlist']['name']
        )
        context['playlist'].save()

    if context['track']['pk']:
        try:
            context['track'] = Track.objects.get(pk=context['track']['pk'])
        except Track.DoesNotExist:
            pass
    elif context['track']['name'] and context['track']['artist']['name']:
        try:
            context['track'] = Track.objects.get(name=context['track']['name'],
                artist__name=context['track']['artist']['name'])
        except Track.DoesNotExist:
            try:
                artist = Artist.objects.get(name=context['track']['artist']['name'])
            except Artist.DoesNotExist:
                artist = Artist(name=context['track']['artist']['name'])
            
            context['track'] = Track(name=context['track']['name'],
                artist=artist)

    if context['action'] == 'add':
        context['user_playlists'] = Playlist.objects.all_with_hidden().filter(
            creation_user=request.user)
    elif context['action'] == 'remove':
        context['user_playlists'] = Playlist.objects.all_with_hidden().filter(
            creation_user=request.user, tracks__name=context['track'].name)

    plname = False
    if isinstance(context['playlist'], dict):
        plname = context['playlist'].get('name', False)
    elif isinstance(context['playlist'], Playlist):
        plname = context['playlist'].name
    if plname and plname.find('hidden:') == 0:
        # select only choice if possible 
        if context['user_playlists'].count() == 1:
            context['playlist'] = context['user_playlists'][0]

    if getattr(context['playlist'], 'name', False) and \
        getattr(context['track'], 'name', False) and \
        request.method == 'POST':

        if not getattr(context['track'].artist, 'pk', False):
            context['track'].artist.save()
            context['track'].artist = context['track'].artist
            print 'saved artist', context['track'].artist, context['track'].artist.pk
        else:
            print 'got artist', context['track'].artist, context['track'].artist.pk

        if not getattr(context['track'], 'pk', False):
            context['track'].youtube_id = context['track'].youtube_get_best()
            context['track'].save()

        try:
            if context['action'] == 'add':
                if context['playlist'].creation_user == request.user:
                    context['playlist'].tracks.add(context['track'])
                else:
                    PlaylistModification(
                        playlist=context['playlist'],
                        creation_user=request.user,
                        track=context['track'],
                        action='add'
                    ).save()
            elif context['action'] == 'remove':
                if context['playlist'].creation_user == request.user:
                    context['playlist'].tracks.remove(context['track'])
                else:
                    PlaylistModification(
                        playlist=context['playlist'],
                        creation_user=request.user,
                        track=context['track'],
                        action='remove'
                    ).save()

            context['status'] = 'success'
            if context['action'] == 'add':
                msg = 'thanks for adding <a href="%s">%s</a> to playlist <a href="%s">%s</a>' % (
                    context['track'].get_absolute_url(),
                    unicode(context['track']),
                    context['playlist'].get_absolute_url(),
                    unicode(context['playlist']),
                )
                if request.user.is_authenticated():
                    if context['playlist'].pk == request.user.playlistprofile.tiny_playlist.pk:
                        action.send(request.user, verb='liked track', action_object=context['track'])
                    else:
                        action.send(request.user, verb='added track to playlist', action_object=context['track'], target=context['playlist'])
            else:
                msg = 'thanks for removing <a href="%s">%s</a> from playlist <a href="%s">%s</a>' % (
                    context['track'].get_absolute_url(),
                    unicode(context['track']),
                    context['playlist'].get_absolute_url(),
                    unicode(context['playlist']),
                )
                # disabled negative actions
#                if request.user.is_authenticated():
#                    if context['playlist'].pk == request.user.playlistprofile.tiny_playlist.pk:
#                        action.send(request.user, verb='unliked track', action_object=context['track'])
#                    else:
#                        action.send(request.user, verb='removed track from playlist', action_object=context['track'], target=context['playlist'])
            messages.add_message(request, messages.INFO, msg)
        except Exception:
            context['status'] = 'error'
            messages.add_message(request, messages.INFO, msg)

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))   

def playlist_category_details(request, slug, parent_slug=None,
    template_name='playlist/category_details.html', extra_context=None):
    context = {}

    if parent_slug:
        context['object'] = shortcuts.get_object_or_404(PlaylistCategory, parent__slug=parent_slug, slug=slug)
    else:
        context['object'] = shortcuts.get_object_or_404(PlaylistCategory, slug=slug)

    context['object_list'] = Playlist.objects.filter(
        Q(category__slug=slug) |
        Q(category__parent__slug=slug)
    ).select_related()

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def playlist_list(request, qs=Playlist.objects.all(),
    template_name='playlist/playlist_list.html', extra_context=None):
    context = {}
    
    context['object_list'] = qs
    s = '''
    select 
        t.id,
        t.name 
    from tagging_taggeditem ti 
    left join tagging_tag t on t.id=ti.tag_id 
    group by t.id, t.name 
    order by count(ti.object_id) desc 
    limit 15
    '''
    context['best_tags'] = Tag.objects.raw(s)

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

@decorators.login_required
def playlist_add(request, form_class=PlaylistAddForm,
    template_name='playlist/playlist_add.html', extra_context=None):
    context = {}

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            object = form.save(commit=False)
            object.creation_user = request.user
            object.save()
            return http.HttpResponseRedirect(object.get_absolute_url())
    else:
        form = form_class()
    
    context['form'] = form

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))

def playlist_details(request, user, slug, default_format=False, qname='term',
    paginate_by=5, 
    template_name='playlist/playlist_details.html', extra_context=None):
    context = {}

    try:
        object = Playlist.objects.all_with_hidden().get(
            creation_user__username=user,
            slug=slug
        )
    except Playlist.DoesNotExist:
        return http.Http404()

    if request.user.is_authenticated():
        serialized = object.to_dict(for_user=request.user)
    else:
        serialized = object.to_dict()

    if request.GET.get('format', default_format) == 'json':
        if object.name[0:7] != 'hidden:' and request.user.is_authenticated():
            request.user.playlistprofile.last_playlist = object
            request.user.playlistprofile.save()
        return http.HttpResponse(simplejson.dumps(serialized))

    context['object'] = object
    if request.user.is_authenticated():
        context['user_tracks'] = object.all_user_tracks(request.user)
    else:
        context['user_tracks'] = object.tracks.all()

    q = request.GET.get(qname, False)
    page = int(request.GET.get('page', 1))
    if q:
        track = Track(name=q)
        track.lastfm_search()
        context['tracks'] = track.matches[(page*paginate_by)-1:(page*paginate_by)-1+paginate_by]
        context['totalPages'] = int(math.ceil(len(track.matches) / paginate_by))
        context['allPages'] = range(1, context['totalPages'] + 1)
        context['currentPage'] = page

    if request.user.is_authenticated():
        context['is_fan'] = request.user.playlistprofile.fanof_playlists.filter(pk=object.pk).count()

    context['playlist_fans_slice'] = context['object'].fans.all()[:20]

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))
