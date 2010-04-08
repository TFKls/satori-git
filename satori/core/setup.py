# vim:ts=4:sts=4:sw=4:expandtab
"""Takes care of settings required by Django. Import this module before django.*
"""

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'satori.core.settings'

from django.core.management import setup_environ
from satori.core import settings

setup_environ(settings)
