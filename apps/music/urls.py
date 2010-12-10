from django.conf.urls.defaults import *

urlpatterns = patterns('music.views',
    url(
        r'search/$',
        'music_search',
        name='music_search'
    ),
)
