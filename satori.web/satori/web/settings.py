# vim:ts=4:sts=4:sw=4:expandtab

# Django settings for satoritest project.

import getpass
import os
PROJECT_PATH = os.path.abspath(os.path.split(__file__)[0])


DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = ''           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = ''             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

USE_SSL = True
THRIFT_HOST = 'dev.satori.tcs.uj.edu.pl'
THRIFT_PORT = 38889
BLOB_PORT = 38887
params = os.environ.get('SATORI_BACKEND', None)
if params:
    params = params.split(':')
    assert len(params) == 3, '$SATORI_BACKEND should be of form host:thrift_port:blob_port'
    THRIFT_HOST = params[0]
    THRIFT_PORT = int(params[1])
    BLOB_PORT = int(params[2])
elif getpass.getuser() == 'gutowski':
    USE_SSL = False
    THRIFT_HOST = 'localhost'
    THRIFT_PORT = 39889
    BLOB_PORT = 39887
elif (getpass.getuser() == 'zzzmwm01') or (getpass.getuser() == 'mwrobel'):
    THRIFT_HOST = 'localhost'
    THRIFT_PORT = 37889
    BLOB_PORT = 37887
#elif getpass.getuser() == 'duraj':
#    USE_SSL = False
#    THRIFT_HOST = 'localhost'
#    THRIFT_PORT = 36889
#    BLOB_PORT = 36887
elif getpass.getuser() == 'boraks':
    USE_SSL = False
    THRIFT_HOST = 'student.tcs.uj.edu.pl'
    THRIFT_PORT = 32889
    BLOB_PORT = 32887
del params

LOGGING = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'default': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                },
            },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                },
            },
        'root': {
            'handlers': ['console'],
            'level': 'DEBUG',
            },
        }

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Warsaw'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'm@i55d12d3la4!*%ba&_^p5tl*!0mqdohef3lm1(q5-%eyuff)'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
#    'django.contrib.sessions.middleware.SessionMiddleware',
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'satori.web.urls'


TEMPLATE_DIRS = (PROJECT_PATH,
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
#    'django.contrib.auth',
#    'django.contrib.contenttypes',
#    'django.contrib.sessions',
#    'django.contrib.sites',
#    'django.contrib.admin',
    'satori.web',
    'django.contrib.webdesign',
)

RECAPTCHA_PUB_KEY = '6LdTPsASAAAAACfINb4O2NltX7I8IeGkBhk8tXJa'
RECAPTCHA_PRIV_KEY = '6LdTPsASAAAAAD0AVU5Jo148Mve24lr6swKPpPwA'

SATORI_TOKEN_COOKIE_NAME = 'satori_token'
SATORI_TOKEN_COOKIE_DOMAIN = None
SATORI_TOKEN_COOKIE_SECURE = False
SATORI_TOKEN_COOKIE_PATH = '/'
SATORI_TOKEN_COOKIE_HTTPONLY = True
