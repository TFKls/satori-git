# vim:ts=4:sts=4:sw=4:expandtab

import satori.client.web.setup



def manage():
    from django.core.management import execute_manager
    import satori.client.web.settings as settings

   	execute_manager(settings)

