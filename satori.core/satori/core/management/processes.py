# vim:ts=4:sts=4:sw=4:expandtab

import logging
from multiprocessing import Process, Semaphore
from multiprocessing.connection import Client, Listener
from time import sleep
import ssl
import os
import signal
import sys

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler

from thrift.protocol.TBinaryProtocol import TBinaryProtocolFactory
from thrift.transport.TSocket import TServerSocket, TSocket
from thrift.transport.TTransport import TFramedTransportFactory, TTransportBase
from thrift.server.TServer import TThreadedServer, TForkingServer

from twisted.web import server, wsgi
from twisted import internet
import twisted.internet.ssl

from satori.core.api      import ars_interface
from satori.core.checking import CheckingMaster
from satori.core.printing import PrintingMaster
from satori.core.dbev.notifier              import run_notifier
from satori.core.management.master_process  import SatoriProcess
from satori.core.thrift_server   import ThriftProcessor
from satori.events        import Slave2, Client2, Master
from satori.events.mapper import TrivialMapper

class TLateInitSSLSocket(TTransportBase):
    def __init__(self, handle):
        self.handle = handle
        self.socket = None

    def getSocket(self):
        if self.socket is None:
            self.handle.do_handshake()
            self.socket = TSocket()
            self.socket.setHandle(self.handle)
        return self.socket

    def isOpen(self):
        return self.getSocket().isOpen()

    def setTimeout(self, ms):
        return self.getSocket().setTimeout(ms)

    def read(self, sz):
        return self.getSocket().read(sz)

    def write(self, sz):
        return self.getSocket().write(sz)

    def flush(self):
        return self.getSocket().flush()

    def close(self):
        if self.socket is None:
            self.handle.close()
        else:
            return self.getSocket().close()
        

class TLateInitSSLServerSocket(TServerSocket):
  SSL_VERSION = ssl.PROTOCOL_TLSv1

  def __init__(self, host=None, port=9090, certfile='cert.pem', unix_socket=None):
    self.setCertfile(certfile)
    TServerSocket.__init__(self, host, port)

  def setCertfile(self, certfile):
    if not os.access(certfile, os.R_OK):
      raise IOError('No such certfile found: %s' % (certfile))
    self.certfile = certfile

  def accept(self):
    plain_client, addr = self.handle.accept()
    try:
      client = ssl.wrap_socket(plain_client, certfile=self.certfile,
                      server_side=True, ssl_version=self.SSL_VERSION,
                      do_handshake_on_connect=False)
    except ssl.SSLError, ssl_exc:
      plain_client.close()
      # We can't raise the exception, because it kills most TServer derived serve()
      # methods.
      # Instead, return None, and let the TServer instance deal with it in
      # other exception handling.  (but TSimpleServer dies anyway)
      return None 
    return TLateInitSSLSocket(client)

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

    def do_handle_signal(self, signum, frame):
        if self.serverpid == os.getpid():
            for child in self.server.children:
                try:
                    os.kill(child, signal.SIGTERM)
                    os.waitpid(child, 0)
                except OSError:
                    pass
        sys.exit(0)

    def do_run(self):
        if settings.USE_SSL:
            socket = TLateInitSSLServerSocket(port=settings.THRIFT_PORT, certfile=settings.SSL_CERTIFICATE)
        else:
            socket = TServerSocket(port=settings.THRIFT_PORT)
#        server = TThreadedServer(ThriftProcessor(), socket, TFramedTransportFactory(), TBinaryProtocolFactory())
        self.serverpid = os.getpid()
        self.server = TForkingServer(ThriftProcessor(), socket, TFramedTransportFactory(), TBinaryProtocolFactory())
        self.server.serve()

class ChainedOpenSSLContextFactory(internet.ssl.DefaultOpenSSLContextFactory):
    def cacheContext(self):
#        super(ChainedOpenSSLContextFactory, self).cacheContext()
#ARGH: Twisted uses old-style classes.
        internet.ssl.DefaultOpenSSLContextFactory.cacheContext(self)
        self._context.use_certificate_chain_file(self.certificateFileName)

class TwistedHttpServerProcess(SatoriProcess):
    def __init__(self):
        super(TwistedHttpServerProcess, self).__init__('http server')

    def do_handle_signal(self, signum, frame):
        internet.reactor.callFromThread(internet.reactor.stop)

    def do_run(self):
        resource = wsgi.WSGIResource(internet.reactor, internet.reactor.getThreadPool(), WSGIHandler())
        if settings.USE_SSL:
            internet.reactor.listenSSL(settings.BLOB_PORT, server.Site(resource), 
                    ChainedOpenSSLContextFactory(settings.SSL_CERTIFICATE, settings.SSL_CERTIFICATE), interface=settings.BLOB_HOST)
        else:
            internet.reactor.listenTCP(settings.BLOB_PORT, server.Site(resource), interface=settings.BLOB_HOST)
        internet.reactor.run()


class UwsgiHttpServerProcess(SatoriProcess):
    def __init__(self):
        super(UwsgiHttpServerProcess, self).__init__('http server')

    def do_run(self):
        options = ['satori: http server (uWSGI)']
        if settings.USE_SSL:
            options.extend(['--https', '{0}:{1},{2},{3}'.format(settings.BLOB_HOST, settings.BLOB_PORT, settings.SSL_CERTIFICATE, settings.SSL_CERTIFICATE)])
        else:
            options.extend(['--http', '{0}:{1}'.format(settings.BLOB_HOST, settings.BLOB_PORT)])
        options.extend(['--master', '--module', 'satori.core.wsgi:application', '--log-date=%F %T,000 - uWSGI - INFO',
            '--disable-logging', '--auto-procname', '--procname-prefix-spaced', 'satori:',
            '--processes', '50', '--http-processes', '10', '--cheaper', '5', '--cheaper-step', '5', '--cheaper-overload', '5',])
        if 'VIRTUAL_ENV' in os.environ:
            options.extend(['--virtualenv', os.environ['VIRTUAL_ENV']])
        os.execvp('uwsgi', options)

    def terminate(self):
        os.kill(self.pid, signal.SIGQUIT)


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


class CheckingMasterProcess(EventSlaveProcess):
    def __init__(self):
        super(CheckingMasterProcess, self).__init__('checking master', [CheckingMaster()])

class PrintingMasterProcess(EventSlaveProcess):
    def __init__(self):
        super(PrintingMasterProcess, self).__init__('printing master', [PrintingMaster()])
