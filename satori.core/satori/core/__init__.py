# vim:ts=4:sts=4:sw=4:expandtab
"""The core of the system. Manages the database and operational logic. Functionality is
exposed over Thrift.
"""

import sys
import os


def manage():
    from django.core.management import execute_manager

    settings_module_name = os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'satori.core.settings')
    __import__(settings_module_name)
    settings_module = sys.modules[settings_module_name]

    # HACK
    import django.core.management

    old_fmm = django.core.management.find_management_module

    def find_management_module(app_name):
        if app_name == 'satori.core':
            return os.path.join(os.path.dirname(__file__), 'management')
        else:
            return old_fmm(app_name)

    django.core.management.find_management_module = find_management_module
    # END OF HACK

    execute_manager(settings_module)

