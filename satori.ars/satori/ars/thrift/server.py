# vim:ts=4:sts=4:sw=4:expandtab
"""Server for the Thrift protocol.
"""

from StringIO import StringIO
from types import ClassType, TypeType

from thrift.server.TServer import TThreadedServer
from thrift.transport.TTransport import TServerTransportBase, TFramedTransportFactory
from thrift.protocol.TBinaryProtocol import TBinaryProtocolFactory

from satori.ars.model import ArsString, ArsProcedure, ArsService, ArsInterface
from satori.objects import Argument

from processor import ThriftProcessor
from writer import ThriftWriter

class ThriftServer(object):

    @Argument('server_type', type=(ClassType, TypeType), default=TThreadedServer)
    @Argument('transport', type=TServerTransportBase)
    @Argument('interface', type=ArsInterface)
    def __init__(self, server_type, transport, interface):
        super(ThriftServer, self).__init__()
        self._server_type = server_type
        self._transport = transport
        self._interface = interface

    def run(self):
        idl_proc = ArsProcedure(return_type=ArsString, name='Server_getIDL')
        idl_serv = ArsService(name='Server')
        idl_serv.add_procedure(idl_proc)
        self._interface.add_service(idl_serv)
        writer = ThriftWriter()
        idl = StringIO()
        writer.write_to(self._interface, idl)
        idl = idl.getvalue()
        idl_proc.implementation = lambda: idl
        processor = ThriftProcessor(self._interface)
        server = self._server_type(processor, self._transport, TFramedTransportFactory(), TBinaryProtocolFactory())
        return server.serve()
