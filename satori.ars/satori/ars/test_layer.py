# vim:ts=4:sts=4:sw=4:expandtab
"""Takes care of settings required by Django. Import this module before django.*
"""

import sys
import new

from django.conf import settings

settings.configure(DATABASE_ENGINE='sqlite3', INSTALLED_APPS=[])

from django.db import connection
from django.test import utils

class DjangoTestLayer(object):
    @classmethod
    def testSetUp(self):
        utils.setup_test_environment()
        self.db_name = connection.creation.create_test_db(verbosity=0, autoclobber=True)

    @classmethod
    def testTearDown(self):
        connection.creation.destroy_test_db(self.db_name, verbosity=0)
        utils.teardown_test_environment()

    @classmethod
    def testTearDown(self):
        from django.core import management
        management.call_command('flush', verbosity=0, interactive=False)

def setup_module(name):
    newmod = new.module(name + '.models')
    newmod.__file__ = sys.modules[name].__file__
    sys.modules[name + '.models'] = newmod
    settings.INSTALLED_APPS.append(name)

