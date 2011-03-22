from django.conf import settings
from django import template
from playlist.models import affinities_betwen, Playlist
from music.models import Recommendation
from actstream.models import Follow
from django.db.models import Sum

register = template.Library()

levels = (
    (29, 'rookie'),
    (99, 'dj'),
    (399, 'rock star'),
    (999, 'guru'),
    (2999, 'idol'),
    (9999999, 'legend'),
    (9999999999999, 'staff'),
)

@register.filter
def get_xp(user):
    points = user.playlistprofile.points or 0
    return points

def get_next_rank(user):
    xp = get_xp(user)
    level = 1
    once = False
    for max_xp, level_rank in levels:
        if xp > max_xp:
            level += 1
            continue
        if once:
            return (level, level_rank)
        else:
            once = True
            continue

    return (7, 'god')

def get_rank(user):
    xp = get_xp(user)
    level = 1
    for max_xp, level_rank in levels:
        if xp > max_xp:
            level += 1
            continue
        return (level, level_rank)

    return (7, 'god')

@register.filter
def get_rank_number(user):
    level = get_rank(user)
    return level[0]

@register.filter
def get_rank_xp(user):
    level = get_rank(user)
    return levels[level[0]-1][0]

@register.filter
def get_rank_text(user):
    level = get_rank(user)
    return level[1]

@register.filter
def get_next_rank_number(user):
    level = get_next_rank(user)
    return level[0]

@register.filter
def get_next_rank_xp(user):
    level = get_next_rank(user)
    return levels[level[0]-1][0]

@register.filter
def get_next_rank_text(user):
    level = get_next_rank(user)
    return level[1]

@register.filter
def get_bar_width(user, max_width):
    xp = float(get_xp(user))
    next_xp = get_next_rank_xp(user)
    width = (xp/next_xp) * max_width
    return int(width)

@register.filter
def affinities_with(a, b):
    if a.__class__.__name__ == 'User':
        a = a.playlistprofile
    if b.__class__.__name__ == 'User':
        b = b.playlistprofile
    return affinities_betwen(a, b)

@register.filter
def affinities_with_class(a, b):
    affinities = affinities_with(a, b)
    if affinities < 26:
        return 'low_afinities'
    if affinities < 50:
        return 'medium_afinities'
    else:
        return 'high_afinities'

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
