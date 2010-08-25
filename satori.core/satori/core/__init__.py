# vim:ts=4:sts=4:sw=4:expandtab
"""The core of the system. Manages the database and operational logic. Functionality is
exposed over Thrift.
"""

import satori.core.setup
import traceback

def export_thrift():
    """Entry Point. Writes the Thrift contract of the server to standard output.
    """
    from sys import stdout
    from satori.ars import wrapper
    import satori.core.api
    from satori.ars.thrift import ThriftWriter
    writer = ThriftWriter()
    writer.writeTo(wrapper.generate_contracts(), stdout)

def start_server_event_master():
    from setproctitle import setproctitle
    setproctitle('satori: event master')
    from multiprocessing.connection import Listener
    from satori.events import Master 
    from satori.events.mapper import TrivialMapper
    listener = Listener(address=(satori.core.setup.settings.EVENT_HOST, satori.core.setup.settings.EVENT_PORT))
    master = Master(mapper=TrivialMapper())
    master.listen(listener)
    print 'event master starting'
    master.run()

def start_server_thrift_server():
    from setproctitle import setproctitle
    setproctitle('satori: thrift server')
    from thrift.transport.TSocket import TServerSocket
    from thrift.server.TServer import TThreadedServer
    from satori.ars import wrapper
    from satori.core import cwrapper
    import satori.core.api
    from satori.ars.thrift import ThriftServer
    wrapper.register_middleware(cwrapper.TransactionMiddleware())
    server = ThriftServer(TThreadedServer, TServerSocket(port=satori.core.setup.settings.THRIFT_PORT), wrapper.generate_contracts())
    print 'thrift server starting'
    server.run()

def start_server_blob_server():
    from setproctitle import setproctitle
    setproctitle('satori: blob server')
    from django.core.handlers.wsgi import WSGIHandler
    from cherrypy.wsgiserver import CherryPyWSGIServer
    server = CherryPyWSGIServer((satori.core.setup.settings.BLOB_HOST, satori.core.setup.settings.BLOB_PORT), WSGIHandler())
    print 'blob server starting'
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


def start_server_dbev_notifier():
    from setproctitle import setproctitle
    setproctitle('satori: dbev notifier')
    from multiprocessing.connection import Client
    from satori.dbev.notifier import notifier
    connection = Client(address=(satori.core.setup.settings.EVENT_HOST, satori.core.setup.settings.EVENT_PORT))
    print 'dbev notifier starting'
    notifier(connection)

def start_server_event_slave():
    from setproctitle import setproctitle
    setproctitle('satori: event slave')
    from multiprocessing.connection import Client
    from satori.events import Slave, QueueId, Attach, Map, Receive
    slave = Slave(connection=Client(address=(satori.core.setup.settings.EVENT_HOST, satori.core.setup.settings.EVENT_PORT)))
    def dump_events():
        queue_id = QueueId("*")
        yield Attach(queue_id)
        mapping = yield Map(dict(), queue_id)
        while True:
            queue, event = yield Receive()
            print 'queue', queue, 'received', event
    slave.schedule(dump_events())
    print 'event slave starting'
    slave.run()

def start_server_judge_dispatcher():
    from setproctitle import setproctitle
    setproctitle('satori: judge dispatcher')
    from multiprocessing.connection import Client
    from satori.events import Slave
    from satori.core.judge_dispatcher import judge_dispatcher
    slave = Slave(connection=Client(address=(satori.core.setup.settings.EVENT_HOST, satori.core.setup.settings.EVENT_PORT)))
    slave.schedule(judge_dispatcher())
    print 'judge dispatcher starting'
    slave.run()

def start_server_judge_generator():
    from setproctitle import setproctitle
    setproctitle('satori: judge generator')
    from multiprocessing.connection import Client
    from satori.events import Slave
    from satori.core.judge_dispatcher import judge_generator
    slave = Slave(connection=Client(address=(satori.core.setup.settings.EVENT_HOST, satori.core.setup.settings.EVENT_PORT)))
    slave.schedule(judge_generator(slave))
    print 'judge generator starting'
    try:
        slave.run()
    except:
        traceback.print_exc()
    print 'judge generator finishing'


def dummy_test():
    from setproctitle import setproctitle
    setproctitle('satori: dummy test')
    from multiprocessing.connection import Client
    from satori.events import Slave
    from satori.core.judge_dispatcher import judge_generator
    from satori.events import QueueId, Attach, Map, Receive, Send, Event
    slave = Slave(connection=Client(address=('localhost', 38888)))

    def gen_1():
        print 'q0'
        yield Attach('q1')
        print 'q1'
        yield Attach('q2')
        print 'q2'
        yield Attach('q3')
        print 'q3'

    def gen_2():
        print 'R0'
        yield Receive()
        print 'R1'
        yield Receive()
        print 'R2'
        yield Receive()
        print 'R3'

    slave.schedule(gen_1())
    slave.schedule(gen_2())
    from time import sleep
    sleep(20)
    print 'dummy test starting'
    slave.run()



def start_server():
    from setproctitle import setproctitle
    setproctitle('satori: master')

    processes = []
    from multiprocessing import Process
    from time import sleep
    
    event_master = Process(target=start_server_event_master)
    event_master.start()
    processes.append(event_master)
    
    sleep(1)

    thrift_server = Process(target=start_server_thrift_server)
    thrift_server.start()
    processes.append(thrift_server)
    
    blob_server = Process(target=start_server_blob_server)
    blob_server.start()
    processes.append(blob_server)
    
    dbev_notifier = Process(target=start_server_dbev_notifier)
    dbev_notifier.start()
    processes.append(dbev_notifier)
    
    event_slave = Process(target=start_server_event_slave)
    event_slave.start()
    processes.append(event_slave)
    
    judge_dispatcher = Process(target=start_server_judge_dispatcher)
    judge_dispatcher.start()
    processes.append(judge_dispatcher)
    
    judge_generator = Process(target=start_server_judge_generator)
    judge_generator.start()
    processes.append(judge_generator)
    
    dummy_testp = Process(target=dummy_test)
    dummy_testp.start()
    processes.append(dummy_testp)
    
    from signal import signal, SIGINT, SIGTERM, pause

    def handle_signal(signum, frame):
        for process in processes:
            process.terminate()
            process.join()
        exit(0)

    signal(SIGINT, handle_signal)
    signal(SIGTERM, handle_signal)
    
    while True:
        pause()

def manage():
    from django.core.management import execute_manager
    import satori.core.settings as settings

    execute_manager(settings)

