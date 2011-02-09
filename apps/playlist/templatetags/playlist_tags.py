from django.conf import settings
from django import template
from playlist.models import affinities_betwen

register = template.Library()

@register.filter
def affinities_with(a, b):
    if a.__class__.__name__ == 'User':
        a = a.playlistprofile
    if b.__class__.__name__ == 'User':
        b = b.playlistprofile
    return affinities_betwen(a, b)

@register.inclusion_tag('playlist/_render_playlists.html')
def render_playlists(playlists):
    return {
        'object_list': playlists,
        'STATIC_URL': settings.STATIC_URL,
    }

@register.inclusion_tag('playlist/_render_playlists.html')
def render_playlist(playlist):
    return {
        'object_list': (playlist,),
        'STATIC_URL': settings.STATIC_URL,
    }
