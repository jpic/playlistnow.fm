import simplejson

from django import http
from django import shortcuts
from django import template
from django.contrib.auth import decorators
from django.db.models import Q

from music.models import *
from models import *
from forms import *

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
            context['playlist'] = Playlist.objects.get(pk=context['playlist']['pk'])
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
        context['user_playlists'] = Playlist.objects.filter(
            creation_user=request.user)
    elif context['action'] == 'remove':
        context['user_playlists'] = Playlist.objects.filter(
            creation_user=request.user, tracks__name=context['track'].name)

    # select only choice if possible
    if context['user_playlists'].count() == 1:
        context['playlist'] = context['user_playlists'][0]

    if getattr(context['playlist'], 'name', False) and \
        getattr(context['track'], 'name', False) and \
        request.method == 'POST':

        if not getattr(context['track'].artist, 'pk', False):
            context['track'].artist.save()
            print 'saved artist', context['track'].artist, context['track'].artist.pk
        else:
            print 'got artist', context['track'].artist, context['track'].artist.pk

        if not getattr(context['track'], 'pk', False):
            context['track'].youtube_id = context['track'].youtube_get_best()
            context['track'].save()

        print context['playlist'].pk, context['track'].pk

        try:
            if context['action'] == 'add':
                context['playlist'].tracks.add(context['track'])
            elif context['action'] == 'remove':
                context['playlist'].tracks.remove(context['track'])
            context['status'] = 'success'
        except Exception:
            context['status'] = 'error'

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
    template_name='playlist/playlist_details.html', extra_context=None):
    context = {}

    object = shortcuts.get_object_or_404(Playlist, creation_user__username=user,slug=slug)
    if request.GET.get('format', default_format) == 'json':
        return http.HttpResponse(simplejson.dumps(object.to_dict()))

    context['object'] = object

    q = request.GET.get(qname, False)
    if q:
        track = Track(name=q)
        track.lastfm_search()
        context['tracks'] = track.matches[:5]

    context.update(extra_context or {})
    return shortcuts.render_to_response(template_name, context,
        context_instance=template.RequestContext(request))
