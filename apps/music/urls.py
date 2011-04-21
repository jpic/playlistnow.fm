from django.conf.urls.defaults import *

# @todo: implement lang ?
urlpatterns = patterns('music.views',
    url(
        r'search/$',
        'music_search',
        name='music_search'
    ),
    url(
        r'recommendation/(?P<id>[0-9]+)/thank/$',
        'music_recommendation_thank',
        name='music_recommendation_thank'
    ),
    url(
        r'recommendation/add/$',
        'music_recommendation_add',
        name='music_recommendation_add'
    ),
    url(
        r'badvideo/$',
        'music_badvideo',
        name='music_badvideo'
    ),
    url(
        r'album/(?P<name>[^/]+)/$',
        'music_album_details',
        name='music_album_details'
    ),
    url(
        r'track/(?P<artist>[^/]+)/(?P<name>[^/]+)/$',
        'music_track_details',
        name='music_track_details'
    ),
    url(
        r'fanship/artist/$',
        'music_artist_fanship',
        name='music_artist_fanship'
    ),
    url(
        r'artist/(?P<name>[^/]+)/$',
        'music_artist_details',
        {
            'tab': 'overview',
        },
        name='music_artist_details'
    ),
    url(
        r'artist/(?P<name>[^/]+)/(?P<tab>\w+)/$',
        'music_artist_details',
        name='music_artist_details_tab'
    ),
    url(
        r'search/autocomplete/$',
        'music_search_autocomplete',
        name='music_search_autocomplete'
    ),
)
