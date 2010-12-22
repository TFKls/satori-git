# vim:ts=4:sts=4:sw=4:expandtab

from   django.conf  import settings
from   django.core.management.base import NoArgsCommand
import logging
from   optparse     import make_option
import os
from   setproctitle import setproctitle
from   signal       import signal, SIGINT, SIGHUP, SIGTERM
import signal       as signal_module
import sys

signalnames = dict((k, v) for v, k in signal_module.__dict__.iteritems() if v.startswith('SIG'))


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        from satori.core.management.master_process import SatoriMasterProcess

        process = SatoriMasterProcess(False)
        process.stop()


