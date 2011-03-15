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
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.humanize',
    
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
    'django_extensions',
    'jpic',
    'pagination',
    'tagging_ext',
    'socialregistration',
    'gfc',
    'actstream',
    'django.contrib.comments',
    'endless_pagination',
]

MIDDLEWARE_CLASSES = [
    'middleware.DynamicHtmlMiddleware',
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
]
INTERNAL_IPS = [
    #'83.38.0.213',
    #'81.36.51.224',
    #'127.0.0.1',
]


CACHES = {
    'default': {
        #'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        #'LOCATION': '/var/tmp/django_cache',
        #'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}
CACHE_BACKEND = 'file:///var/tmp/django_cache'


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

LASTFM_API_KEY = 'a67b55859d8b3cf1ed3bb2c9a5c59898'
LASTFM_API_SECRET = 'c7970cc5b664b1b1e19a3f471ebc1b12'

TWITTER_CONSUMER_KEY = '61g88FE8bBXLDwck7gaRlA'
TWITTER_CONSUMER_SECRET_KEY = '4Tza4RltIdTgBODWdCflfGWFlIRtbFIL1bBz7Z7OBE'
TWITTER_REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'
TWITTER_ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'
TWITTER_AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'

FACEBOOK_APP_ID = '117753378295717'
FACEBOOK_API_KEY = '738ca1d67fa0e795c8a5604278278e8e'
FACEBOOK_SECRET_KEY = '5068add1ba6569c0ed1ecbba4e8f6f56'

GOOGLE_SITE_ID = '09173394585243409353'

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

#EMAIL_HOST="localhost"
