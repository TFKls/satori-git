# vim:ts=4:sts=4:sw=4:expandtab
"""Django settings for satori.core.
"""
import getpass
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2'
DATABASE_NAME = getpass.getuser()
DATABASE_USER = ''
DATABASE_PASSWORD = ''
DATABASE_HOST = ''
DATABASE_PORT = ''

CACHE_BACKEND = 'memcached://localhost:11211'

EVENT_HOST = 'localhost'
EVENT_PORT = 38888
THRIFT_HOST = '0.0.0.0'
THRIFT_PORT = 38889
BLOB_HOST = '0.0.0.0'
BLOB_PORT = 38887

BLOB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'tmp', 'blob')

if getpass.getuser() == 'gutowski':
    EVENT_PORT = 39888
    THRIFT_PORT = 39889
    BLOB_PORT = 39887
if (getpass.getuser() == 'zzzmwm01') or (getpass.getuser() == 'mwrobel'):
    EVENT_PORT = 37888
    THRIFT_PORT = 37889
    BLOB_PORT = 37887
if getpass.getuser() == 'duraj':
    EVENT_PORT = 36888
    THRIFT_PORT = 36889
    BLOB_PORT = 36887

ADMIN_NAME = 'admin'
ADMIN_PASSWORD = 'admin'

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
SECRET_KEY = 'j&_^(#r7-zzp5w7&gv2gl*qea8)5o9d+fxhvon7xc_l1x-a0eh'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'satori.core.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'satori.dbev',
    'satori.core',
)
