from thrift.transport.TSocket import TSocket
from satori.ars.thrift import ThriftReader, ThriftClient
from satori.ars import ars2py

transport = TSocket(host='localhost', port=38889)
reader = ThriftReader()
reader.readFrom(open('satori.thrift'))
client = ThriftClient(transport)
client.contracts = reader.contracts
client.start()
ars2py.process(reader)

globals().update(ars2py.classes)

def start_console():
    import code
    import readline
    console = code.InteractiveConsole()
    console.runcode('import satori.client.common as satori_classes')
    print
    print 'satori.client.common is imported as satori_classes'
    print
    console.interact()

