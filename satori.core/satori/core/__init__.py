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
    writer.contracts.update(wrapper.generate_contracts().items)
    writer.writeTo(stdout)

def start_server_event_master():
    from setproctitle import setproctitle
    setproctitle('satori: event master')
    from multiprocessing.connection import Listener
    from satori.events import Master 
    from satori.events.mapper import TrivialMapper
    listener = Listener(address=('localhost', 38888))
    master = Master(mapper=TrivialMapper())
    master.listen(listener)
    print 'event master starting'
    master.run()

def start_server_thrift_server():
    from setproctitle import setproctitle
    setproctitle('satori: thrift server')
    from thrift.transport.TSocket import TServerSocket
    from satori.ars import wrapper
    from satori.core import cwrapper
    import satori.core.api
    from satori.ars.thrift import ThriftServer
    wrapper.register_middleware(cwrapper.TransactionMiddleware())
    server = ThriftServer(transport=TServerSocket(port=38889))
    server.contracts.update(wrapper.generate_contracts().items)
    print 'thrift server starting'
    server.run()

def start_server_dbev_notifier():
    from setproctitle import setproctitle
    setproctitle('satori: dbev notifier')
    from multiprocessing.connection import Client
    from satori.dbev.notifier import notifier
    connection = Client(address=('localhost', 38888))
    print 'dbev notifier starting'
    notifier(connection)

def start_server_event_slave():
    from setproctitle import setproctitle
    setproctitle('satori: event slave')
    from multiprocessing.connection import Client
    from satori.events import Slave, QueueId, Attach, Map, Receive
    slave = Slave(connection=Client(address=('localhost', 38888)))
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
    slave = Slave(connection=Client(address=('localhost', 38888)))
    slave.schedule(judge_dispatcher())
    print 'judge dispatcher starting'
    slave.run()

def start_server_judge_generator():
    from setproctitle import setproctitle
    setproctitle('satori: judge generator')
    from multiprocessing.connection import Client
    from satori.events import Slave
    from satori.core.judge_dispatcher import judge_generator
    slave = Slave(connection=Client(address=('localhost', 38888)))
    slave.schedule(judge_generator())
    print 'judge generator starting'
    try:
        slave.run()
    except:
        traceback.print_exc()
    print 'judge generator finishing'

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
    
    from signal import signal, SIGINT, SIGTERM, pause

    def handle_signal(signum, frame):
        for process in processes:
            process.terminate()
            process.join()
        exit(0)

#    signal(SIGINT, handle_signal)
    signal(SIGTERM, handle_signal)
    
    while True:
        pause()

def manage():
    from django.core.management import execute_manager
    import satori.core.settings as settings

   	execute_manager(settings)

