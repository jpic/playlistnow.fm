from django.conf.urls.defaults import *

# @todo: implement lang ?

urlpatterns = patterns('music.views',
    url(
        r'search/$',
        'music_search',
        name='music_search'
    ),
    url(
        r'album/(?P<name>[^/]*)/$',
        'music_album_details',
        name='music_album_details'
    ),
    url(
        r'track/(?P<artist>.*)/(?P<name>.*)/$',
        'music_track_details',
        name='music_track_details'
    ),
    url(
        r'artist/(?P<name>[^/]*)/$',
        'music_artist_details',
        name='music_artist_details'
    ),
    url(
        r'find/$',
        'music_find',
        name='music_find'
    ),
    url(
        r'search/autocomplete/$',
        'music_search_autocomplete',
        name='music_search_autocomplete'
    ),
)

urlpatterns += patterns ('',
    url(
        r'player/frame/$',
        'django.views.generic.simple.direct_to_template',
        {
            'template': 'music/player_frame.html',
        },
        name='music_player_frame'
    ),
    url(
        r'player/frameset/$',
        'django.views.generic.simple.direct_to_template',
        {
            'template': 'music/player_frameset.html',
        },
        name='music_player_frameset'
    ),
)
