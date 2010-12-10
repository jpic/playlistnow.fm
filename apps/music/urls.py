from django.conf.urls.defaults import *

urlpatterns = patterns('music.views',
    url(
        r'search/$',
        'music_search',
        name='music_search'
    ),
    url(
        r'search/autocomplete/$',
        'music_search',
        kwargs={
            'template_name': 'music/search_autocomplete.html',
        },
        name='music_search_autocomplete'
    ),
)
