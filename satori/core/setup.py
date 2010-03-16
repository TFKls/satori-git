"""Takes care of settings required by Django. Import this module before django.*
"""

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'satori.core.settings'

from django.core.management import setup_environ
from satori.core import settings

setup_environ(settings)