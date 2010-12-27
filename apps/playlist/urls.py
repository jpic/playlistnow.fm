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
