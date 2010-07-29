# vim:ts=4:sts=4:sw=4:expandtab
"""The core of the system. Manages the database and operational logic. Functionality is
exposed over Thrift.
"""

import satori.core.setup

def export_thrift():
    """Entry Point. Writes the Thrift contract of the server to standard output.
    """
    from sys import stdout
    import satori.core.models
    from satori.ars import wrapper
    import satori.core.sec
    from satori.ars.thrift import ThriftWriter
    writer = ThriftWriter()
    writer.contracts.update(wrapper.generate_contracts().items)
    writer.writeTo(stdout)


def start_server():
    """Entry Point. Starts the core server.
    """
    from threading import Thread
    from multiprocessing.connection import Listener, Client
    from satori.dbev.notifier import notifier
    from satori.events import Master, Slave, QueueId, Attach, Map, Receive
    from satori.events.mapper import TrivialMapper
    listener = Listener(address=('localhost', 38888))
    master = Master(mapper=TrivialMapper())
    master.listen(listener)
    master_thread = Thread(target=master.run)
    master_thread.daemon = True
    master_thread.start()
    print 'event master started'
    
    from sys import exit
    from multiprocessing import Process
    from thrift.transport.TSocket import TServerSocket
    import satori.core.models
    from satori.ars import wrapper
    import satori.core.sec
    from satori.ars.thrift import ThriftServer
    server = ThriftServer(transport=TServerSocket(port=38889))
    server.contracts.update(wrapper.generate_contracts().items)
    server_process = Process(target=server.run)
    server_process.start()
    print 'thrift server started'

    print 'connecting to event master'
    connection = Client(address=('localhost', 38888))
    print 'connected!'
    notifier_thread = Thread(target=notifier, args=(connection,))
    notifier_thread.start()
    print 'database notifier started'
    
    from signal import signal, SIGINT, SIGTERM, pause
    def handle_signal(signum, frame):
        server_process.terminate()
        listener.close()
        exit(0)
    signal(SIGINT, handle_signal)
    signal(SIGTERM, handle_signal)
    
    slave = Slave(connection=Client(address=('localhost', 38888)))
    def dump_events():
        queue_id = QueueId("*")
        yield Attach(queue_id)
        mapping = yield Map(dict(), queue_id)
        while True:
            queue, event = yield Receive()
            print 'queue', queue, 'received', event
    slave.schedule(dump_events())
    print 'starting event slave'
    slave.run()
    print 'event slave quit!'
    #while True:
    #    pause()

def manage():
    from django.core.management import execute_manager
    import satori.core.settings as settings

   	execute_manager(settings)

