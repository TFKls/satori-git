# vim:ts=4:sts=4:sw=4:expandtab

from   cherrypy.wsgiserver import CherryPyWSGIServer
from   datetime    import datetime
from   django.conf import settings
from   django.core.handlers.wsgi import WSGIHandler
import errno
import fcntl
import logging
from   multiprocessing import Process, Semaphore
from   multiprocessing.connection import Client, Listener
import sys
import os
from   time         import sleep
from   setproctitle import setproctitle
from   signal       import signal, getsignal, SIGINT, SIGTERM, SIGHUP, pause
import signal       as signal_module
from   thrift.transport.TSocket import TServerSocket
from   thrift.server.TServer    import TThreadedServer

from satori.ars.thrift    import ThriftServer
from satori.core.api      import ars_interface
from satori.core.checking.check_queue       import CheckQueue
from satori.core.checking.dispatcher_runner import DispatcherRunner
from satori.core.dbev.notifier              import run_notifier
from satori.core.management.master_process  import SatoriProcess
from satori.events        import Slave2, Client2, Master
from satori.events.mapper import TrivialMapper


class EventMasterProcess(SatoriProcess):
    def __init__(self):
        super(EventMasterProcess, self).__init__('event master')
        self.sem = Semaphore(0)

    def do_run(self):
        listener = Listener(address=(settings.EVENT_HOST, settings.EVENT_PORT))
        master = Master(mapper=TrivialMapper())
        master.listen(listener)
        self.sem.release()
        master.run()

    def start(self, *args, **kwargs):
        super(EventMasterProcess, self).start(*args, **kwargs)
        while True:
            if self.sem.acquire(False):
                return
            if not self.is_alive():
                raise RuntimeError('Event master failed to start')
            sleep(0)


class EventSlaveProcess(SatoriProcess):
    def __init__(self, name, clients):
        super(EventSlaveProcess, self).__init__(name)
        self.clients = clients

    def do_handle_signal(self, signum, frame):
        self.slave.terminate()

    def do_run(self):
        self.slave = Slave2(connection=Client(address=(settings.EVENT_HOST, settings.EVENT_PORT)))
        for client in self.clients:
            self.slave.add_client(client)
        self.slave.run()


class ThriftServerProcess(SatoriProcess):
    def __init__(self):
        super(ThriftServerProcess, self).__init__('thrift server')

    def do_run(self):
        server = ThriftServer(TThreadedServer, TServerSocket(port=settings.THRIFT_PORT), ars_interface)
        server.run()


class BlobServerProcess(SatoriProcess):
    def __init__(self):
        super(BlobServerProcess, self).__init__('blob server')

    def do_handle_signal(self, signum, frame):
        self.server.stop()

    def do_run(self):
        self.server = CherryPyWSGIServer((settings.BLOB_HOST, settings.BLOB_PORT), WSGIHandler())
        self.server.start()


class DbevNotifierProcess(SatoriProcess):
    def __init__(self):
        super(DbevNotifierProcess, self).__init__('dbev notifier')

    def do_run(self):
        connection = Client(address=(settings.EVENT_HOST, settings.EVENT_PORT))
        run_notifier(Slave2(connection))


class DebugQueue(Client2):
    queue = 'debug_queue'
    def init(self):
        self.attach(self.queue)
        self.map({}, self.queue)

    def handle_event(self, queue, event):
        logging.debug('Debug event: %s', event)


class DebugQueueProcess(EventSlaveProcess):
    def __init__(self):
        super(DebugQueueProcess, self).__init__('debug queue', [DebugQueue()])


class CheckQueueProcess(EventSlaveProcess):
    def __init__(self):
        super(CheckQueueProcess, self).__init__('check queue', [CheckQueue()])


class DispatcherRunnerProcess(EventSlaveProcess):
    def __init__(self):
        super(DispatcherRunnerProcess, self).__init__('debug queue', [DispatcherRunner()])
