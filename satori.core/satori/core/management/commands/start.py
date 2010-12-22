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
    option_list = NoArgsCommand.option_list + (
        make_option('--daemon', action='store_true', dest='daemon', default=False,
            help='Creates a daemon process.'),
    )

    def handle_noargs(self, **options):
        setproctitle('satori: foreground')
       
        from satori.core.management.master_process import SatoriMasterProcess

        daemon = options.get('daemon', False)

        process = SatoriMasterProcess(daemon)

        if daemon:
            process.start()

            # do not call atexit
            os._exit(0)
        else:
            def handle_signal(signum, frame):
                print 'foreground caught signal {0}'.format(signalnames.get(signum, signum))
                process.terminate()

            signal(SIGINT, handle_signal)
            signal(SIGHUP, handle_signal)
            signal(SIGTERM, handle_signal)
        
            process.start()

            process.join()


