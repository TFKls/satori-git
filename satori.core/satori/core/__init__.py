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
    from satori.ars import django_
    from satori.ars.thrift import ThriftWriter
    django_.generate_contracts()
    writer = ThriftWriter()
    writer.contracts.update(django_.contract_list.items)
    writer.writeTo(stdout)


def start_server():
    """Entry Point. Starts the core server.
    """
    from threading import Thread
    from multiprocessing.connection import Listener
    from satori.events import Master
    from satori.events.mapper import TrivialMapper
    listener = Listener(address=('localhost', 38888))
    master = Master(mapper=TrivialMapper())
    master.listen(listener)
    master_thread = Thread(target=master.run)
    master_thread.daemon = True
    master_thread.start()
    
    from sys import exit
    from multiprocessing import Process
    from thrift.transport.TSocket import TServerSocket
    import satori.core.models
    from satori.ars import django_
    from satori.ars.thrift import ThriftServer
    django_.generate_contracts()
    server = ThriftServer(transport=TServerSocket(port=38889))
    server.contracts.update(django_.contract_list.items)
    server_process = Process(target=server.run)
    server_process.start()
    
    from signal import signal, SIGINT, SIGTERM, pause
    def handle_signal(signum, frame):
        server_process.terminate()
        listener.close()
        exit(0)
    signal(SIGINT, handle_signal)
    signal(SIGTERM, handle_signal)
    
    while True:
        pause()

def manage():
    from django.core.management import execute_manager
    import satori.core.settings as settings

   	execute_manager(settings)

