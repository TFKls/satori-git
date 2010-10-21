# vim:ts=4:sts=4:sw=4:expandtab
"""Server for the Thrift protocol.
"""

from types import ClassType, TypeType

from thrift.server.TServer import TThreadedServer
from thrift.transport.TTransport import TServerTransportBase, TFramedTransportFactory
from thrift.protocol.TBinaryProtocol import TBinaryProtocolFactory

from satori.ars.model import ArsInterface
from satori.objects import Argument

from processor import ThriftProcessor

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
        processor = ThriftProcessor(self._interface)
        server = self._server_type(processor, self._transport, TFramedTransportFactory(), TBinaryProtocolFactory())
        return server.serve()
