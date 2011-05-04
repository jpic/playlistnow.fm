from django.conf.urls.defaults import *

urlpatterns = patterns('radio.views',
    url(
        r'artist/(?P<name>.*)/$',
        'radio_artist',
        name='radio_artist'
    ),
)
