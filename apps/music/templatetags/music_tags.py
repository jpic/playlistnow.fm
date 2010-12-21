from django import template

register = template.Library()

@register.inclusion_tag('music/_render_track.html')
def render_track(track, youtube):
    return {
        'youtube': youtube,
        'track': track,
    }
