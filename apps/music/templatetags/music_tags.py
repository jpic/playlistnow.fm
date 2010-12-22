from django import template

register = template.Library()

@register.inclusion_tag('music/_render_tracks.html')
def render_tracks(tracks):
    return {
        'tracks': tracks,
    }

@register.inclusion_tag('music/_render_tracks.html')
def render_track(track):
    return {
        'tracks': (track,)
    }
