# vim:ts=4:sts=4:sw=4:expandtab
"""The core of the system. Manages the database and operational logic. Functionality is
exposed over Thrift.
"""

import sys
import os
import traceback
from time import sleep
from datetime import datetime
from multiprocessing import Process 
from multiprocessing.connection import Client, Listener
from setproctitle import setproctitle
import signal as signal_module
from signal import signal, getsignal, SIGINT, SIGTERM, pause
from satori.events import Slave2, Client2

import satori.core.entities

signalnames = dict((k, v) for v, k in signal_module.__dict__.iteritems() if v.startswith('SIG'))

class SatoriProcess(Process):
    def __init__(self, name):
        super(SatoriProcess, self).__init__()
        self.name = name
    
    def do_handle_signal(self, signum, frame):
        sys.exit()

    def handle_signal(self, signum, frame):
        print '{0} caught signal {1}'.format(self.name, signalnames.get(signum, signum))
        self.do_handle_signal(signum, frame)

    def run(self):
        os.setsid()
        setproctitle('satori: {0}'.format(self.name))

        signal(SIGTERM, self.handle_signal)

        print '{0} starting'.format(self.name)

        try:
            self.do_run()
        except:
            print '{0} exited with error'.format(self.name)
            traceback.print_exc()
        else:
            print '{0} exited'.format(self.name)


class EventSlaveProcess(SatoriProcess):
    def __init__(self, name, clients):
        super(EventSlaveProcess, self).__init__(name)
        self.clients = clients

    def do_handle_signal(self, signum, frame):
        self.slave.terminate()

    def do_run(self):
        from django.conf import settings
        self.slave = Slave2(connection=Client(address=(settings.EVENT_HOST, settings.EVENT_PORT)))
        for client in self.clients:
            self.slave.add_client(client)
        self.slave.run()

class EventMasterProcess(SatoriProcess):
    def __init__(self):
        super(EventMasterProcess, self).__init__('event master')

    def do_run(self):
        from django.conf import settings
        from satori.events import Master
        from satori.events.mapper import TrivialMapper
        listener = Listener(address=(settings.EVENT_HOST, settings.EVENT_PORT))
        master = Master(mapper=TrivialMapper())
        master.listen(listener)
        master.run()

class DebugQueue(Client2):
    queue = 'debug_queue'
    def init(self):
        self.attach(self.queue)
        self.map({}, self.queue)

    def handle_event(self, queue, event):
        print datetime.now(), event

class ThriftServerProcess(SatoriProcess):
    def __init__(self):
        super(ThriftServerProcess, self).__init__('thrift server')

    def do_run(self):
        from django.conf import settings
        from thrift.transport.TSocket import TServerSocket
        from thrift.server.TServer import TThreadedServer
        from satori.ars.thrift import ThriftServer
        from satori.core.api import ars_interface

        server = ThriftServer(TThreadedServer, TServerSocket(port=settings.THRIFT_PORT), ars_interface)
        server.run()

class BlobServerProcess(SatoriProcess):
    def __init__(self):
        super(BlobServerProcess, self).__init__('blob server')

    def do_handle_signal(self, signum, frame):
        self.server.stop()

    def do_run(self):
        from django.conf import settings
        from django.core.handlers.wsgi import WSGIHandler
        from cherrypy.wsgiserver import CherryPyWSGIServer
        self.server = CherryPyWSGIServer((settings.BLOB_HOST, settings.BLOB_PORT), WSGIHandler())
        self.server.start()

class DbevNotifierProcess(SatoriProcess):
    def __init__(self):
        super(DbevNotifierProcess, self).__init__('dbev notifier')

    def do_run(self):
        from django.conf import settings
        from satori.dbev.notifier import run_notifier
        connection = Client(address=(settings.EVENT_HOST, settings.EVENT_PORT))
        run_notifier(Slave2(connection))

def export_thrift():
    """Entry Point. Writes the Thrift interface of the server to standard output.
    """
    os.environ['DJANGO_SETTINGS_MODULE'] = 'satori.core.settings'

    from satori.ars.thrift import ThriftWriter
    from satori.core.api import ars_interface

    writer = ThriftWriter()
    writer.write_to(ars_interface, sys.stdout)

def start_server():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'satori.core.settings'

    setproctitle('satori: master')

    print 'Loading ARS interface...'
    import satori.core.api
    print 'ARS interface loaded.'

    from satori.core.checking.check_queue import CheckQueue
    from satori.core.checking.dispatcher_runner import DispatcherRunner

    to_start = [
            EventMasterProcess(), 
            EventSlaveProcess('debug queue', [DebugQueue()]), 
            DbevNotifierProcess(), 
            EventSlaveProcess('check queue', [CheckQueue()]),
            EventSlaveProcess('dispatcher runner', [DispatcherRunner()]),
            ThriftServerProcess(),
            BlobServerProcess(),
    ]

    started = []

    def handle_signal(signum, frame):
        for process in reversed(started):
            process.terminate()
            process.join()
        exit(0)

    signal(SIGINT, handle_signal)
    signal(SIGTERM, handle_signal)

    for process in to_start:
        process.start()
        started.append(process)
        if isinstance(process, EventMasterProcess):
            sleep(1)

    while True:
        sleep(1)

def manage():
    from django.core.management import execute_manager
    import satori.core.settings

    execute_manager(satori.core.settings)

