# vim:ts=4:sts=4:sw=4:expandtab
"""Client for the Thrift protocol.
"""

import errno
import threading
import socket
from types import FunctionType

from thrift.transport.TTransport import TFramedTransport, TTransportException
from thrift.protocol.TBinaryProtocol import TBinaryProtocol

from satori.ars.model import ArsInterface
from satori.objects import Argument, Signature, ArgumentMode

from processor import ThriftProcessor

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
            except TTransportException:
                self.stop()
                self.start()
                return self._processor.call(procedure, values.named, self._protocol, self._protocol)
            except IOError as e:
                if e[0] == errno.EPIPE:
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

        self._transport = TFramedTransport(self._transport_factory())
        self._transport.open()
        self._protocol = TBinaryProtocol(self._transport)
        self._processor = ThriftProcessor(self._interface)
        self._started = True

    def stop(self):
        if self._started:
            self._transport.close()
            self._started = False


