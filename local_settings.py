# -*- coding: utf-8 -*-

DATABASES = {
    "default": {
        "ENGINE": "postgresql_psycopg2", # Add "postgresql_psycopg2", "postgresql", "mysql", "sqlite3" or "oracle".
        "password": "MBzdUqeStHXd13VllGudNgBiFb1HGg",                       # Or path to database file if using sqlite3.
        "USER": "pln.yourlabs.org",                             # Not used with sqlite3.
        "NAME": "pln.yourlabs.org",                         # Not used with sqlite3.
        "HOST": "",                             # Set to empty string for localhost. Not used with sqlite3.
        "PORT": "",                             # Set to empty string for default. Not used with sqlite3.
    }
}


INSTALLED_APPS = [
    # Admin-tools
    'admin_tools.theming',
    'admin_tools.menu',
    'admin_tools.dashboard',

    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.humanize",
    
    "pinax.templatetags",
    
    # external
    "staticfiles",
    "debug_toolbar",
    "mailer",
    "uni_form",
    "django_openid",
    "ajax_validation",
    "timezones",
    "emailconfirmation",
    
    # Pinax
    "pinax.apps.account",
    "pinax.apps.signup_codes",
    
    # project
    "about",

    "tagging",
    "music",
    "playlist",
    "django_extensions",
    "jpic",
    "pagination",
    "tagging_ext",
    "socialregistration",
    "gfc",
    "actstream",
]

MIDDLEWARE_CLASSES = [
    "middleware.DynamicHtmlMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_openid.consumer.SessionConsumer",
    "django.contrib.messages.middleware.MessageMiddleware",
    "pinax.apps.account.middleware.LocaleMiddleware",
    "pinax.middleware.security.HideSensistiveFieldsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "pagination.middleware.PaginationMiddleware",
    "socialregistration.middleware.FacebookMiddleware",
]

CACHES = {
    'default': {

        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
    }
}
CACHE_BACKEND = 'file:///var/tmp/django_cache'


OPENID_REDIRECT_NEXT = '/accounts/openid/done/'

OPENID_SREG = {"requred": "nickname, email, fullname",
               "optional":"postcode, country",
               "policy_url": ""}

#example should be something more like the real thing, i think
OPENID_AX = [{"type_uri": "http://axschema.org/contact/email",
              "count": 1,
              "required": True,
              "alias": "email"},
             {"type_uri": "http://axschema.org/schema/fullname",
              "count":1 ,
              "required": False,
              "alias": "fname"}]

OPENID_AX_PROVIDER_MAP = {'Google': {'email': 'http://axschema.org/contact/email',
                                     'firstname': 'http://axschema.org/namePerson/first',
                                     'lastname': 'http://axschema.org/namePerson/last'},
                          'Default': {'email': 'http://axschema.org/contact/email',
                                      'fullname': 'http://axschema.org/namePerson',
                                      'nickname': 'http://axschema.org/namePerson/friendly'}
                          }


ADMIN_TOOLS_MENU = 'menu.CustomMenu'

LASTFM_API_KEY = 'a67b55859d8b3cf1ed3bb2c9a5c59898'
LASTFM_API_SECRET = 'c7970cc5b664b1b1e19a3f471ebc1b12'

TWITTER_CONSUMER_KEY = 'CmjacxzweBzBy1w1Rr1Q5g'
TWITTER_CONSUMER_SECRET_KEY = 'j2Jx2Iz0JQn0WASJFPfifijVBewC1D2h3vbQI25zc'
TWITTER_REQUEST_TOKEN_URL = 'http://api.twitter.com/oauth/request_token'
TWITTER_ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
TWITTER_AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'


FACEBOOK_APP_ID = '117753378295717'
FACEBOOK_API_KEY = '738ca1d67fa0e795c8a5604278278e8e'
FACEBOOK_SECRET_KEY = '5068add1ba6569c0ed1ecbba4e8f6f56'

GOOGLE_SITE_ID = '09173394585243409353'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'socialregistration.auth.FacebookAuth',
    'socialregistration.auth.TwitterAuth',
    'socialregistration.auth.OpenIDAuth',
    'gfc.auth.GfcAuth',
)

UI_IGNORE_URLS = (
    '/socialregistration/facebook/login/',
    '/admin',
    '/site_media',
    '/socialregistration/twitter',
    '/socialregistration/setup/',
    '/gfc/redirect',
    '/socialregistration/facebook/connect',
)

GENERATE_USERNAME = True
SOCIALREGISTRATION_GENERATE_USERNAME = True

AJAX_NAVIGATION = True
LOGIN_REDIRECT_URL = '/postlogin'

