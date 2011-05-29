# -*- coding: utf-8 -*-

import logging
import os.path
LOG_FILE=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'log', 'django.log'))
hdlr = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('[%(asctime)s]%(levelname)-8s"%(message)s"','%Y-%m-%d %a %H:%M:%S') 

hdlr.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(hdlr)
logger.setLevel(logging.NOTSET)


PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))

from socket import gethostname; HOSTNAME=gethostname()

if PROJECT_PATH == '/home/srv/beta.playlistnow.fm/main':
    DATABASES = {
        'default': {
            'ENGINE': 'mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
            'PASSWORD': 'stnh23stnhBEUNT32',                       # Or path to database file if using sqlite3.
            'USER': 'beta',                             # Not used with sqlite3.
            'NAME': 'beta_pln',                         # Not used with sqlite3.
            'HOST': '',                             # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '',                             # Set to empty string for default. Not used with sqlite3.
        }
    }
elif PROJECT_PATH == '/home/srv/playlistnow.fm/main':
    DATABASES = {
        'default': {
            'ENGINE': 'mysql', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
            'PASSWORD': 'stnthSTNSTNHSHTNEUSTNhsNTHN2323',                       # Or path to database file if using sqlite3.
            'USER': 'prod',                             # Not used with sqlite3.
            'NAME': 'prod_pln',                         # Not used with sqlite3.
            'HOST': '',                             # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '',                             # Set to empty string for default. Not used with sqlite3.
        }
    }
elif PROJECT_PATH == '/home/srv/pln.yourlabs.org/main':
    DATABASES = {
        'default': {
            'ENGINE': 'postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
            'password': 'MBzdUqeStHXd13VllGudNgBiFb1HGg',                       # Or path to database file if using sqlite3.
            'USER': 'pln.yourlabs.org',                             # Not used with sqlite3.
            'NAME': 'pln.yourlabs.org',                         # Not used with sqlite3.
            'HOST': '',                             # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '',                             # Set to empty string for default. Not used with sqlite3.
        }
    }


INSTALLED_APPS = [
    # Admin-tools
    'admin_tools.theming',
    'admin_tools.menu',
    'admin_tools.dashboard',

    # Django
    'django.contrib.markup',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    
    'pinax.templatetags',
    
    # external
    'notification', # must be first
    'staticfiles',
    'debug_toolbar',
    'mailer',
    'uni_form',
    'django_openid',
    'ajax_validation',
    'timezones',
    'emailconfirmation',
    
    # Pinax
    'pinax.apps.account',
    'pinax.apps.signup_codes',
    
    # project
    'about',

    'tagging',
    'music',
    'playlist',
    'radio',
    'django_extensions',
    'jpic',
    'pagination',
    'tagging_ext',
    'socialregistration',
    'gfc',
    'robots',
    'actstream',
    'django.contrib.comments',
    'endless_pagination',

    'sentry.client',
]

MIDDLEWARE_CLASSES = [
    'middleware.DynamicHtmlMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_openid.consumer.SessionConsumer',
    'django.contrib.messages.middleware.MessageMiddleware',
    'pinax.apps.account.middleware.LocaleMiddleware',
    'pinax.middleware.security.HideSensistiveFieldsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'socialregistration.middleware.FacebookMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'middleware.OldUrlsMiddleware',
]
INTERNAL_IPS = [
    '79.159.156.87',
]
if PROJECT_PATH == '/home/srv/playlistnow.fm/main':
    CACHE_BACKEND = "memcached://127.0.0.1:11211/"
    CACHE_MIDDLEWARE_SECONDS = 60
    CACHE_MIDDLEWARE_KEY_PREFIX = 'prod'
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
        }
    }
elif PROJECT_PATH == '/home/srv/beta.playlistnow.fm/main':
    CACHE_BACKEND = "memcached://127.0.0.1:11211/"
    CACHE_MIDDLEWARE_SECONDS = 60
    CACHE_MIDDLEWARE_KEY_PREFIX = 'prod'
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
        }
    }

OPENID_REDIRECT_NEXT = '/accounts/openid/done/'

OPENID_SREG = {'requred': 'nickname, email, fullname',
               'optional':'postcode, country',
               'policy_url': ''}

#example should be something more like the real thing, i think
OPENID_AX = [{'type_uri': 'http://axschema.org/contact/email',
              'count': 1,
              'required': True,
              'alias': 'email'},
             {'type_uri': 'http://axschema.org/schema/fullname',
              'count':1 ,
              'required': False,
              'alias': 'fname'}]

OPENID_AX_PROVIDER_MAP = {'Google': {'email': 'http://axschema.org/contact/email',
                                     'firstname': 'http://axschema.org/namePerson/first',
                                     'lastname': 'http://axschema.org/namePerson/last'},
                          'Default': {'email': 'http://axschema.org/contact/email',
                                      'fullname': 'http://axschema.org/namePerson',
                                      'nickname': 'http://axschema.org/namePerson/friendly'}
                          }


ADMIN_TOOLS_MENU = 'menu.CustomMenu'

LASTFM_API_KEY = '645b4f357740c4759d67a78bb5a864d7'
LASTFM_API_SECRET = 'deae62b2d89e744ab30be459af2ca293'
#LASTFM_API_KEY = 'a67b55859d8b3cf1ed3bb2c9a5c59898'
#LASTFM_API_SECRET = 'c7970cc5b664b1b1e19a3f471ebc1b12'

TWITTER_CONSUMER_KEY = '5p5RXWbnJQFBtSlBz2ftA'
TWITTER_CONSUMER_SECRET_KEY = 'QVCspo9tn84X4e11WTGjdDoJtjsJm9LVdih5RY794'
#beta
#TWITTER_CONSUMER_KEY = 'p252OYzorJKGyYZ2wDLpQ'
#TWITTER_CONSUMER_SECRET_KEY = 'IZinFz5Ul4mWFvxMySil97jaXKDnlebWTfFf3bQHU'
TWITTER_REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
TWITTER_ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
TWITTER_AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'

FACEBOOK_APP_ID = '86928100945'
FACEBOOK_API_KEY = 'deb205b1c3050bd7ae82c4bbc3772c59'
FACEBOOK_SECRET_KEY = '0cb9e1d29fe6d86be0cecab93106fffe'

if PROJECT_PATH == '/home/srv/beta.playlistnow.fm/main':
    GOOGLE_SITE_ID = '08546160909140751983'
elif PROJECT_PATH == '/home/srv/playlistnow.fm/main':
    GOOGLE_SITE_ID = '01734141454554986527'

AUTHENTICATION_BACKENDS = (
    'backends.ModelBackend',
    'socialregistration.auth.FacebookAuth',
    'socialregistration.auth.TwitterAuth',
    'socialregistration.auth.OpenIDAuth',
    'gfc.auth.GfcAuth',
)

UI_IGNORE_URLS = (
    '/admin',
    '/site_media',
    '/robots.txt',
    
    '/gfc/redirect',
    '/gfc/callback',
    
    '/account/logout/',

    '/socialregistration/facebook/login/',
    '/socialregistration/facebook/connect',
    '/socialregistration/twitter',
    #'/socialregistration/setup',
    '/registration/userdata',
    '/music/badvideo',
)

GENERATE_USERNAME = False
SOCIALREGISTRATION_GENERATE_USERNAME = GENERATE_USERNAME

AJAX_NAVIGATION = True
LOGIN_REDIRECT_URL = '/me/'
FACEBOOK_OFFLINE_ACCESS = True

ACCOUNT_EMAIL_VERIFICATION = False
ACCOUNT_UNIQUE_EMAIL = EMAIL_CONFIRMATION_UNIQUE_EMAIL = False
ACCOUNT_EMAIL_AUTHENTICATION = False

FORCE_SCRIPT_NAME=''
ENDLESS_PAGINATION_TEMPLATE_VARNAME='template_name'
ENDLESS_PAGINATION_PER_PAGE=4


TIME_ZONE = "Europe/Paris"

ROBOTS_USE_SITEMAP = False

EMAIL_SUBJECT_PREFIX='[PlaylistNow.fm] '
DEFAULT_FROM_EMAIL='PlaylistNow.fm <noreply@playlistnow.fm>'
SERVER_EMAIL='noreply@playlistnow.fm'

ADMINS = [
    ('James Pic', 'jamespic@gmail.com'),
    ('Jonathan Younes', 'sms2night@gmail.com'),
]
if PROJECT_PATH == '/home/srv/beta.playlistnow.fm/main':
    DEBUG=True
    TEMPLATE_DEBUG=True
elif PROJECT_PATH == '/home/srv/playlistnow.fm/main':
    DEBUG=False
    TEMPLATE_DEBUG=False
SEND_BROKEN_LINK_EMAILS=True

USER_LEVELS = (
    (29, 'rookie'),
    (99, 'dj'),
    (399, 'rock star'),
    (999, 'guru'),
    (2999, 'idol'),
    (9999999, 'legend'),
    (9999999999999, 'staff'),
)

SONGKICK_API_KEY='lVqjxnUkqkXuBXDi'
SONGKICK_URL='http://api.songkick.com/api/3.0/events.json?apikey=%s' % SONGKICK_API_KEY

SENTRY_KEY = 'ENUTntheou)(098eu)(E0U983$@#$@34342oasuth90$#@$#@'
SENTRY_REMOTE_URL = 'http://beta.yourlabs.org/sentry/store/'
