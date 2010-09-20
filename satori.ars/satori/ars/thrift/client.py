# vim:ts=4:sts=4:sw=4:expandtab
"""Client for the Thrift protocol.
"""

from StringIO import StringIO
import threading
import socket
from types import FunctionType

from thrift.protocol.TBinaryProtocol import TBinaryProtocol

from satori.objects import Argument, Signature, ArgumentMode
from satori.ars.model import ArsString, ArsProcedure, ArsService, ArsInterface

from processor import ThriftProcessor
from reader import ThriftReader

class ThriftClient(threading.local):
    @Argument('interface', type=ArsInterface)
    @Argument('transport_factory', type=FunctionType)
    def __init__(self, interface, transport_factory):
        super(ThriftClient, self).__init__()
        self._interface = interface
        self._transport_factory = transport_factory
        self._started = False

    def _wrap_procedure(self, procedure):
        names = [parameter.name for parameter in procedure.parameters]
        sign = Signature(names)
        for param in procedure.parameters:
            if param.optional:
            	sign.arguments[param.name].mode = ArgumentMode.OPTIONAL
        values_type = sign.Values

        def proc(*args, **kwargs):
            if not self._started:
            	self.start()

            values = values_type(*args, **kwargs)
            try:
                return self._processor.call(procedure, values.named, self._protocol, self._protocol)
            except socket.error as e:
                if e[0] == 32:
                	self.stop()
                	self.start()
                    return self._processor.call(procedure, values.named, self._protocol, self._protocol)
                else:
                	raise

        proc.func_name = procedure.name
        return proc

    def wrap_all(self):
        for service in self._interface.services:
            for procedure in service.procedures:
                procedure.implementation = self._wrap_procedure(procedure)

    def unwrap_all(self):
        for service in self._interface.services:
            for procedure in service.procedures:
                procedure.implementation = None

    def start(self):
        if self._started:
        	self.stop()
        	
        self._transport = self._transport_factory()
        self._transport.open()
        self._protocol = TBinaryProtocol(self._transport)
        self._processor = ThriftProcessor(self._interface)
        self._started = True

    def stop(self):
        if self._started:
            self._transport.close()
            self._started = False


@Argument('transport_factory', type=FunctionType)
def bootstrap_thrift_client(transport_factory):
    interface = ArsInterface()
    idl_proc = ArsProcedure(return_type=ArsString, name='Server_getIDL')
    idl_serv = ArsService(name='Server')
    idl_serv.add_procedure(idl_proc)
    interface.add_service(idl_serv)

    bootstrap_client = ThriftClient(interface, transport_factory)
    bootstrap_client.wrap_all()
    idl = idl_proc.implementation()
    bootstrap_client.stop()
    
    idl_reader = ThriftReader()
    interface = idl_reader.read_from_string(idl)

    client = ThriftClient(interface, transport_factory)
    client.wrap_all()

    return (interface, client)

