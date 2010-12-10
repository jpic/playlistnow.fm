from django.conf.urls.defaults import *

urlpatterns = patterns('playlist.views',
    url(
        r'add/$',
        'playlist_add',
        name='playlist_add'
    ),
    url(
        r'details/(?P<slug>[^/]*)/$',
        'playlist_details',
        name='playlist_details'
    ),
)
