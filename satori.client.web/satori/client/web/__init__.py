# vim:ts=4:sts=4:sw=4:expandtab
"""The core of the system. Manages the database and operational logic. Functionality is
exposed over Thrift.
"""

import satori.client.web.setup



def manage():
    from django.core.management import execute_manager
    import satori.client.web.settings as settings

   	execute_manager(settings)

