from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

from pinax.apps.account.openid_consumer import PinaxConsumer

import views

handler500 = "pinax.views.server_error"


urlpatterns = patterns("",
    url(r"^$", direct_to_template, {
        "template": "homepage.html",
    }, name="home"),
    url(r"^empty/$", views.empty, name="empty"),
    url(r"^admin/invite_user/$", "pinax.apps.signup_codes.views.admin_invite_user", name="admin_invite_user"),
    url(r"^admin/", include(admin.site.urls)),
    url(r"^about/", include("about.urls")),
    url(r"^account/", include("pinax.apps.account.urls")),
    url(r"^openid/(.*)", PinaxConsumer()),

    url(r'^admin_tools/', include('admin_tools.urls')),
    url(r'^playlist/', include('playlist.urls')),
    url(r'^music/', include('music.urls')),
    url(
        r'^tags/(?P<slug>[^/]+)/$', 
        views.tag_details,
        name='tag_details'
    ),
    url(
        r'^(?P<slug>[^/]+)/$', 
        views.user_details,
        name='user_details'
    ),
)


if settings.SERVE_MEDIA:
    urlpatterns += patterns("",
        url(r"", include("staticfiles.urls")),
    )
