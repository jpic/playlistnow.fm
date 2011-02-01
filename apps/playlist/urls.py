from django.conf.urls.defaults import *
from django.db.models import Count

from models import Playlist

urlpatterns = patterns('playlist.views',
    url(
        r'list/top/$',
        'playlist_list', {
            'qs': Playlist.objects \
                          .annotate(fans_count=Count('fans')) \
                          .order_by('-fans_count'),
        }, name='playlist_list_top'
    ),
    url(
        r'list/$',
        'playlist_list',
        name='playlist_list'
    ),
    url(
        r'category/(?P<slug>[^/]+)/$',
        'playlist_category_details',
        name='playlist_category_details'
    ),
    url(
        r'category/(?P<parent_slug>[^/]+)/(?P<slug>[^/]+)/$',
        'playlist_category_details',
        name='playlist_category_details_with_parent'
    ),
    url(
        r'track_modify/$',
        'playlist_track_modify',
        name='playlist_track_modify'
    ),
    url(
        r'search/autocomplete/$',
        'playlist_search_autocomplete',
        name='playlist_search_autocomplete'
    ),
    url(
        r'search/$',
        'playlist_search',
        name='playlist_search'
    ),
    url(
        r'add/$',
        'playlist_add',
        name='playlist_add'
    ),
    url(
        r'fanship/(?P<playlist_pk>[0-9]+)/$',
        'playlist_fanship',
        name='playlist_fanship'
    ),
    url(
        r'(?P<user>[^/]+)/(?P<slug>[^/]+)/$',
        'playlist_details',
        name='playlist_details'
    ),
)
