from django.conf.urls.defaults import *

urlpatterns = patterns('playlist.views',
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
        r'add/$',
        'playlist_add',
        name='playlist_add'
    ),
    url(
        r'(?P<user>[^/]+)/(?P<slug>[^/]+)/$',
        'playlist_details',
        name='playlist_details'
    ),
)
