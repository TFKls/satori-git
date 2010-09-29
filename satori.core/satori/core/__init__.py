# vim:ts=4:sts=4:sw=4:expandtab
"""The core of the system. Manages the database and operational logic. Functionality is
exposed over Thrift.
"""

import traceback

def get_ars_interface():
    from satori.ars import wrapper
    from satori.core import cwrapper
    import satori.core.api
    if not wrapper.middleware:
        wrapper.register_middleware(cwrapper.TransactionMiddleware())
        wrapper.register_middleware(cwrapper.TokenVerifyMiddleware())
        wrapper.register_middleware(wrapper.TypeConversionMiddleware())
        wrapper.register_middleware(cwrapper.CheckRightsMiddleware())
    return wrapper.generate_interface()

def export_thrift():
    """Entry Point. Writes the Thrift contract of the server to standard output.
    """
    import os
    os.environ['DJANGO_SETTINGS_MODULE'] = 'satori.core.settings'
    from sys import stdout
    from satori.ars.thrift import ThriftWriter
    writer = ThriftWriter()
    writer.write_to(get_ars_interface(), stdout)

def start_server_event_master():
    from django.conf import settings
    from setproctitle import setproctitle
    setproctitle('satori: event master')
    from multiprocessing.connection import Listener
    from satori.events import Master 
    from satori.events.mapper import TrivialMapper
    listener = Listener(address=(settings.EVENT_HOST, settings.EVENT_PORT))
    master = Master(mapper=TrivialMapper())
    master.listen(listener)
    print 'event master starting'
    master.run()

def start_server_thrift_server():
    from django.conf import settings
    from setproctitle import setproctitle
    setproctitle('satori: thrift server')
    from thrift.transport.TSocket import TServerSocket
    from thrift.server.TServer import TThreadedServer
    from satori.ars.thrift import ThriftServer
    server = ThriftServer(TThreadedServer, TServerSocket(port=settings.THRIFT_PORT), get_ars_interface())
    print 'thrift server starting'
    server.run()

def start_server_blob_server():
    from django.conf import settings
    from setproctitle import setproctitle
    setproctitle('satori: blob server')
    from django.core.handlers.wsgi import WSGIHandler
    from cherrypy.wsgiserver import CherryPyWSGIServer
    server = CherryPyWSGIServer((settings.BLOB_HOST, settings.BLOB_PORT), WSGIHandler())
    print 'blob server starting'
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


def start_server_dbev_notifier():
    from django.conf import settings
    from setproctitle import setproctitle
    setproctitle('satori: dbev notifier')
    from multiprocessing.connection import Client
    from satori.dbev.notifier import notifier
    connection = Client(address=(settings.EVENT_HOST, settings.EVENT_PORT))
    print 'dbev notifier starting'
    notifier(connection)

def start_server_event_slave():
    from django.conf import settings
    from setproctitle import setproctitle
    setproctitle('satori: event slave')
    from multiprocessing.connection import Client
    from satori.events import Slave, QueueId, Attach, Map, Receive
    slave = Slave(connection=Client(address=(settings.EVENT_HOST, settings.EVENT_PORT)))
    def dump_events():
        queue_id = QueueId("*")
        yield Attach(queue_id)
        mapping = yield Map(dict(), queue_id)
        while True:
            queue, event = yield Receive()
            #print 'queue', queue, 'received', event
    slave.schedule(dump_events())
    print 'event slave starting'
    slave.run()

def start_server_judge_dispatcher():
    from django.conf import settings
    from setproctitle import setproctitle
    setproctitle('satori: judge dispatcher')
    from multiprocessing.connection import Client
    from satori.events import Slave2
    from satori.core.judge_dispatcher import JudgeDispatcher
    slave = Slave2(connection=Client(address=(settings.EVENT_HOST, settings.EVENT_PORT)))
    slave.add_client(JudgeDispatcher())
    print 'judge dispatcher starting'
    slave.run()

def start_server_judge_generator():
    from django.conf import settings
    from setproctitle import setproctitle
    setproctitle('satori: judge generator')
    from multiprocessing.connection import Client
    from satori.events import Slave2
    from satori.core.judge_dispatcher import JudgeGenerator
    slave = Slave2(connection=Client(address=(settings.EVENT_HOST, settings.EVENT_PORT)))
    slave.add_client(JudgeGenerator())
    print 'judge generator starting'
    try:
        slave.run()
    except:
        traceback.print_exc()
    print 'judge generator finishing'


def start_server():
    import os
    os.environ['DJANGO_SETTINGS_MODULE'] = 'satori.core.settings'

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
    import satori.core.settings

    execute_manager(satori.core.settings)

