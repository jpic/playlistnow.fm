from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

from pinax.apps.account.openid_consumer import PinaxConsumer

import views

handler500 = "pinax.views.server_error"


urlpatterns = patterns("",
    url(
        r'^$',
        'music.views.music_search', {
            'template_name': 'homepage.html',
        },
        name='music_search'
    ),
# deprecating
#    url(
#        r'^socialregistration/google/friendconnect/do/$',
#        direct_to_template, {
#            'template': 'google_friendconnect/do.html',
#        },
#        name='google_friendconnect_do'
#    ),
#    url(
#        r'^popup/auth/$',
#        direct_to_template, {
#            'template': 'popup/auth.html',
#        },
#        name='popup_auth'
#    ),
    url(r"^empty/$", views.empty, name="empty"),
    url(r"^admin/invite_user/$", "pinax.apps.signup_codes.views.admin_invite_user", name="admin_invite_user"),
    url(r"^admin/", include(admin.site.urls)),
    url(r"^about/", include("about.urls")),
    url(r"^gfc/", include("gfc.urls")),
    url(r'^comments/', include('django.contrib.comments.urls')),
    url(r"^socialregistration/", include("socialregistration.urls")),
    url(r"^account/", include("pinax.apps.account.urls")),
    url(r"^openid/(.*)", PinaxConsumer()),

    url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'^playlist/', include('playlist.urls')),
    url(r'^music/', include('music.urls')),
    url('^activity/', include('actstream.urls')),
    url(
        r'^me/$', 
        views.postlogin,
        name='postlogin'
    ),
    url(
        r'^postregistration/$', 
        views.postregistration,
        name='postregistration'
    ),
    url(
        r'^importfriends/$', 
        views.importfriends,
        name='importfriends'
    ),
    url(
        r'^tags/(?P<slug>[^/]+)/$', 
        views.tag_details,
        name='tag_details'
    ),
    url(
        r'^users/(?P<slug>[^/]+)/$', 
        views.user_details,
        {
            'tab': 'activities',
        },
        name='user_details'
    ),
    url(
        r'^users/(?P<slug>[^/]+)/(?P<tab>\w+)/$', 
        views.user_details,
        name='user_details_tab'
    ),

)


if settings.SERVE_MEDIA:
    urlpatterns += patterns("",
        url(r"", include("staticfiles.urls")),
    )
