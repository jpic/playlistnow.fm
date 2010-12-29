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
]

ADMIN_TOOLS_MENU = 'menu.CustomMenu'

LASTFM_API_KEY = 'a67b55859d8b3cf1ed3bb2c9a5c59898'
LASTFM_API_SECRET = 'c7970cc5b664b1b1e19a3f471ebc1b12'

CACHES = {
    'default': {

        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
    }
}
CACHE_BACKEND = 'file:///var/tmp/django_cache'
