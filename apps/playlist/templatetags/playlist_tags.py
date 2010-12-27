from django import template

register = template.Library()

@register.inclusion_tag('playlist/_render_playlists.html')
def render_playlists(playlists):
    return {
        'object_list': playlists,
    }

@register.inclusion_tag('playlist/_render_playlists.html')
def render_playlist(playlist):
    return {
        'object_list': (playlist,)
    }
