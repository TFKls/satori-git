from thrift.transport.TSocket import TSocket
from satori.ars.thrift import ThriftReader, ThriftClient
from satori.ars import ars2py
from threading import local

class Classes(local):
    def __init__(self, host, port):
        self._port = port
        self._host = host

        self._transport = None
        self._client = None
        self._classes = {}

    def __getattr__(self, name):
        if self._client is None:
            self._transport = TSocket(host=self._host, port=self._port)
            self._client = ThriftClient(self._transport)
            self._client.start(bootstrap=True)
            self._classes = ars2py.process(self._client.contracts)

        if name in self._classes:
            return self._classes[name]
        else:
            raise AttributeError('\'Classes\' object has no attribute \'{0}\''.format(name))
       
classes = Classes('localhost', 38889)

def start_console():
    import code
    import readline
    console = code.InteractiveConsole()
    console.runcode('import satori.client.common')
    console.runcode('satori_classes = satori.client.common.classes')
    print
    print 'satori.client.common.classes is imported as satori_classes'
    print
    console.interact()

