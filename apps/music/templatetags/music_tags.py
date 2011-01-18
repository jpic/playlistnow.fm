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
    context = {
        'tracks': tracks,
        'playlist': playlist,
        'request': request,
    }

    return context

@register.inclusion_tag('music/_render_tracks.html')
def render_track(track, playlist=None, request=None):
    return {
        'tracks': (track,),
        'playlist': playlist,
        'request': request,
    }
