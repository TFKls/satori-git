# vim:ts=4:sts=4:sw=4:expandtab

from   django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        from satori.core.management.master_process import SatoriMasterProcess

        process = SatoriMasterProcess(False)
        process.stop()


