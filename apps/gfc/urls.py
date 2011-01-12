from django.conf.urls.defaults import *

urlpatterns = patterns('gfc.views',
    url(
        r'^callback/$',
        'gfc_callback',
        name='gfc_callback',
    ),
    url(
        r'^redirect/$',
        'gfc_redirect',
        name='gfc_redirect',
    ),
)
