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
)

@register.filter
def get_xp(user):
    points = Follow.objects.filter(object_id=user.pk).count()
    fans = Playlist.objects.filter(creation_user=user).aggregate(Sum('fans'))['fans__sum']
    if fans:
        points += fans * 3
    points += Recommendation.objects.filter(source=user, thanks=True).count()
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

    return (7, 'staff')

def get_rank(user):
    xp = get_xp(user)
    level = 1
    for max_xp, level_rank in levels:
        if xp > max_xp:
            level += 1
            continue
        return (level, level_rank)

    return (7, 'staff')

@register.filter
def get_next_rank_integer(user):
    level = get_next_rank(user)
    return level[0]

@register.filter
def get_next_rank_text(user):
    level = get_next_rank(user)
    return level[1]

@register.filter
def get_rank_integer(user):
    level = get_rank(user)
    return level[0]

@register.filter
def get_rank_text(user):
    level = get_rank(user)
    return level[1]

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
