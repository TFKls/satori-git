# vim:ts=4:sts=4:sw=4:expandtab
"""Django settings for satori.core.
"""
import getpass
import os

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

ACTIVATION_REQUIRED = True
EMAIL_HOST = 'localhost'
ACTIVATION_EMAIL_FROM = 'szymon.borak@tcs.uj.edu.pl'
ACTIVATION_EMAIL_SUBJECT = 'Your Satori account activation'
ACTIVATION_EMAIL_BODY = """
Hello {name}!
To activate your Satori account visit http://szymon.borak.student.tcs.uj.edu.pl/activate/{code} .
Your activation token is: {code} .
"""

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': getpass.getuser(),
            'HOST': 'db.tcs.uj.edu.pl',
            'OPTIONS': {
                'autocommit': True,
                },
            },
        }

CACHE_BACKEND = 'memcached://localhost:11211'

EVENT_HOST = 'localhost'
EVENT_PORT = 32888
THRIFT_HOST = '0.0.0.0'
THRIFT_PORT = 32889
BLOB_HOST = '0.0.0.0'
BLOB_PORT = 32887

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

BLOB_DIR = os.path.join(BASE_DIR, 'tmp', 'blob')
LOG_FILE = os.path.join(BASE_DIR, 'tmp', 'server.log')
PID_FILE = os.path.join(BASE_DIR, 'tmp', 'server.pid')

USE_SSL = False
SSL_CERTIFICATE = ''

if getpass.getuser() == 'gutowski':
    EVENT_PORT = 39888
    THRIFT_PORT = 39889
    BLOB_PORT = 39887
if getpass.getuser() == 'zzzmwm01':
    EVENT_PORT = 37888
    THRIFT_PORT = 37889
    BLOB_PORT = 37887
    USE_SSL = True
    SSL_CERTIFICATE = '/home/zzzmwm01/satori/ssl/server.pem'
if getpass.getuser() == 'duraj':
    EVENT_PORT = 36888
    THRIFT_PORT = 36889
    BLOB_PORT = 36887

ADMIN_NAME = 'admin'
ADMIN_PASSWORD = 'admin'

CHECKERS = [ ('checker', 'checker', '0.0.0.0', '0.0.0.0') ]

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
    'satori.core',
)

SECRET_GOOGLE_SPREADSHEET_SERVICE = 'https://docs.google.com/macros/exec?service='
