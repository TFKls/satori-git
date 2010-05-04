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
