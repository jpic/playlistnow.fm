import simplejson
import math

from django import http
from django import shortcuts
from django import template
from django.contrib import messages
from django.core.cache import cache
from django.contrib.auth import decorators
from django.db.models import Q
from tagging.models import Tag
from actstream import action

from music.views import return_json
from music.models import *
from models import *
from forms import *

def playlist_playtrack(request):
    if not request.method == 'POST':
        return http.HttpResponseForbidden()
    playlist_pk = request.POST.get('playlist_pk', False)
    if not playlist_pk:
        return http.HttpResponseBadRequest()
    try:
        playlist = Playlist.objects.get(pk=playlist_pk)
    except Playlist.DoesNotExist:
        return http.HttpResponseBadRequest()
    if playlist.creation_user != request.user:
        key = 'user_points_%s' % playlist.creation_user.pk
        day_points = cache.get(key)
        if not day_points:
            day_points = 1
        else:
            day_points += 1
        cache.set(key, day_points)
        if day_points <= 10:
            playlist.creation_user.playlistprofile.points += 1
            playlist.creation_user.playlistprofile.save()
    return http.HttpResponse()

@decorators.login_required
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
        'action': request.REQUEST.get('action', 'add'),
        'status': None,
        'playlist': {
                'pk': request.REQUEST.get('playlist_pk', False),
                'name': request.REQUEST.get('playlist_name', False),
        },
        'track': {
            'artist': {
                'pk': request.REQUEST.get('artist_pk', False),
                'name': request.REQUEST.get('artist_name', False),
            },
            'pk': request.REQUEST.get('track_pk', False),
            'name': request.REQUEST.get('track_name', False),
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
    
    if not isinstance(context['track'], Track):
        if context['track']['artist']:
            context['track'] = get_or_fake_track(context['track']['name'],
                context['track']['artist']['name'])
        else:
            context['track'] = get_or_fake_track(context['track']['name'])

    if context['action'] == 'add':
        context['user_playlists'] = Playlist.objects.all_with_hidden().filter(
            creation_user=request.user)
    elif context['action'] == 'remove':
        context['user_playlists'] = Playlist.objects.all_with_hidden().filter(
            creation_user=request.user, tracks__name__iexact=context['track'].name)

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

        save_if_fake_track(context['track'])

        if not getattr(context['track'], 'youtube_id', False):
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
            messages.add_message(request, messages.INFO, msg)
        #except Exception:
            #context['status'] = 'error'
            #messages.add_message(request, messages.INFO, msg)
        except User.DoesNotExist:
            pass

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

def playlist_search_autocomplete(request, qname='query', qs=Playlist.objects.all()):
    if not request.GET.get(qname, False):
        return return_json()

    q = request.GET[qname]

    response = {
        'query': request.GET[qname].encode('utf-8'),
        'suggestions': [],
        'data': [],
    }
    
    playlist_search_url = urlresolvers.reverse('playlist_search')

    qs = qs.filter(name__icontains=q)
    qs = qs.distinct('name')
    for playlist in qs[:15]:
        response['suggestions'].append(playlist.name)
        response['data'].append({
            'url': '%s?term=%s' % (playlist_search_url, playlist.name),
            'html': '%s' % (
                playlist.name,
            )
        })

    return return_json(response)

def playlist_search(request,
    template_name='playlist/playlist_search.html', extra_context=None):
    qs1 = Playlist.objects.filter(
        Q(name__icontains=request.GET.get('term', '')) &
        Q(tags__icontains=request.GET.get('term', ''))
    )
    qs2 = Playlist.objects.filter(
        Q(name__icontains=request.GET.get('term', ''))
    ).exclude(id__in=qs1.values_list('id'))
    qs3 = Playlist.objects.filter(
        Q(name__icontains=request.GET.get('term', ''))
    ).exclude(id__in=qs1.values_list('id')).exclude(id__in=qs2.values_list('id'))

    context = {
        'term': request.GET.get('term', ''),
    }
    context['object_list'] = []
    for o in qs1:
        context['object_list'].append(o)
    for o in qs2:
        context['object_list'].append(o)
    for o in qs3:
        context['object_list'].append(o)
    context.update(extra_context or {})
    return playlist_list(request, extra_context=context)

def playlist_list(request, qs=Playlist.objects.all(),
    template_name='playlist/playlist_list.html', extra_context=None):
    context = {}
    
    context['object_list'] = qs.select_related(depth=3)

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
        object.play_counter += 1
        object.save()
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

    context['playlist_fans_slice'] = context['object'].fans.all().select_related()[:20]

    context['you_may_also_like'] = []
    if request.user.is_authenticated():
       context['you_may_also_like'] += Track.objects.filter(
            playlistmodification__playlist=object,
            playlistmodification__creation_user__pk__in=
                request.user.follow_set.all().values_list('object_id', flat=True)
        )

    if len(context['you_may_also_like']) < 8:
        context['you_may_also_like'] += Track.objects.filter(
            playlistmodification__playlist=object
        ).exclude(
            pk__in=[t.pk for t in context['you_may_also_like']]
        )
    
    context['you_may_also_like'] = context['you_may_also_like'][:8]

#    random_tracks = context['user_tracks']
#    i = 0
#    while i < len(random_tracks) and len(context['you_may_also_like']) < 12:
#        track = random_tracks[i]
#        track.lastfm_get_similar()
#        context['you_may_also_like'] += track.similar[:12]
#        i += 1

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))
