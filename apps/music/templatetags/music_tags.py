import math

from django import template

register = template.Library()

@register.inclusion_tag('music/_render_tracks.html')
def render_tracks(tracks, playlist=None, paginateBy=None):
    context = {
        'tracks': tracks,
        'playlist': playlist,
        'paginateBy': paginateBy,
    }

    if paginateBy > 0:
        context['totalPages'] = int(math.ceil(len(tracks) / paginateBy))
        context['allPages'] = range(1, context['totalPages'] + 1)

        i = 0
        page = 1
        for track in tracks:
            if i == paginateBy:
                i = 1
                page += 1
            else:
                i += 1
            
            track.page = page

    return context

@register.inclusion_tag('music/_render_tracks.html')
def render_track(track, playlist=None):
    return {
        'tracks': (track,),
        'playlist': playlist,
    }
