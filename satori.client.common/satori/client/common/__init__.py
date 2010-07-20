from thrift.transport.TSocket import TSocket
from satori.ars.thrift import ThriftReader, ThriftClient
from satori.ars import ars2py
from threading import local

transport = TSocket(host='localhost', port=38889)
client = ThriftClient(transport)
client.start(bootstrap=True)

globals().update(ars2py.process(client.contracts))

#class Classes(local):
#    def __init__(self, host, port):
#        self._port = _port
#        self._host = _host
#
#        self._transport = None
#        self._client = None





def start_console():
    import code
    import readline
    console = code.InteractiveConsole()
    console.runcode('import satori.client.common as satori_classes')
    print
    print 'satori.client.common is imported as satori_classes'
    print
    console.interact()

