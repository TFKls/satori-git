# vim:ts=4:sts=4:sw=4:expandtab

import os
import satori.web.setup

def manage():
    from django.core.management import execute_manager
    import satori.web.settings as settings

    # HACK
    import django.core.management

    old_fmm = django.core.management.find_management_module

    def find_management_module(app_name):
        if app_name == 'satori.web':
            return os.path.join(os.path.dirname(__file__), 'management')
        else:
            return old_fmm(app_name)

    django.core.management.find_management_module = find_management_module
    # END OF HACK

    execute_manager(settings)
