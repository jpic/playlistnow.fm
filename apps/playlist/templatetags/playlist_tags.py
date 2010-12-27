from django.conf import settings
from django import template

register = template.Library()

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
