import math

from django import template

register = template.Library()

@register.inclusion_tag('music/_render_artists.html')
def render_artists(artists, playlist=None):
    context = {
        'artists': artists,
    }

    return context

@register.inclusion_tag('music/_render_artists.html')
def render_artist(artist, playlist=None):
    return {
        'artists': (artist,),
    }

@register.inclusion_tag('music/_render_tracks.html')
def render_tracks(tracks, playlist=None, request=None):
    if not hasattr(request, 'tiny_tracks'):
        if request.user.is_authenticated() and not hasattr(request, 'tiny_tracks'):
            request.tiny_tracks = request.user.playlistprofile.tiny_playlist.tracks.all()
        else:
            request.tiny_tracks = []

    context = {
        'tracks': tracks,
        'playlist': playlist,
        'request': request,
    }

    return context

@register.inclusion_tag('music/_render_tracks.html')
def render_track(track, playlist=None, request=None):
    if not hasattr(request, 'tiny_tracks'):
        if request.user.is_authenticated() and not hasattr(request, 'tiny_tracks'):
            request.tiny_tracks = request.user.playlistprofile.tiny_playlist.tracks.all()
        else:
            request.tiny_tracks = []

    return {
        'tracks': (track,),
        'playlist': playlist,
        'request': request,
    }
