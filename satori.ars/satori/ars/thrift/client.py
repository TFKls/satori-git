# vim:ts=4:sts=4:sw=4:expandtab
"""Client for the Thrift protocol.
"""

from __future__ import absolute_import

import errno
import threading
import socket
from types import FunctionType
from six.moves.http_client import HTTPConnection, HTTPSConnection, HTTPException

from thrift.Thrift import TType, TProcessor, TMessageType, TApplicationException
from thrift.transport.TTransport import TFramedTransport, TTransportException, TMemoryBuffer
from thrift.protocol.TBinaryProtocol import TBinaryProtocol
from thrift.protocol.TCompactProtocol import TCompactProtocol

from satori.ars.model import ArsInterface
from satori.objects import Argument, Signature, ArgumentMode
from satori.objects import Argument, DispatchOn, Signature, Namespace

from satori.ars.thrift.processor import ThriftProcessor

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


class ThriftHttpClient(threading.local):
    def __init__(self, interface, host, port, ssl):
        super(ThriftHttpClient, self).__init__()
        self._interface = interface
        self._host = host
        self._port = port
        self._ssl = ssl
        self._started = False
        self._url = "/thrift"

    def call(self, procedure, args):
        if isinstance(procedure, str):
            try:
                procedure = processor._procedures[procedure]
            except KeyError:
                raise TApplicationException(TApplicationException.UNKNOWN_METHOD,
                    "Unknown method '{0}'".format(name))

        otrans = TMemoryBuffer()
        oproto = TBinaryProtocol(otrans)

#        perf.begin('send')
        oproto.writeMessageBegin(procedure.name, TMessageType.CALL, self._processor.seqid)
        self._processor.seqid = self._processor.seqid + 1
        self._processor.send_struct(Namespace(args), procedure.parameters_struct, oproto)
        oproto.writeMessageEnd()
#        perf.end('send')

        self._http.request('POST', self._url, otrans.getvalue(), {})
        resp = self._http.getresponse()
        data = resp.read()
        iproto = TBinaryProtocol(TMemoryBuffer(data))

#        perf.begin('wait')
        (fname, mtype, rseqid) = iproto.readMessageBegin()
#        perf.end('wait')

#        perf.begin('recv')
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iproto)
            iproto.readMessageEnd()
            x.args = (x.message,)
            raise x
        result = self._processor.recv_struct(procedure.results_struct, iproto)
        iproto.readMessageEnd()
#        perf.end('recv')
#        perf.end('call')

        if result.result is not None:
            return result.result

        for field in procedure.results_struct.fields:
            if getattr(result, field.name) is not None:
                raise getattr(result, field.name)

        return None
#       previous line not compatible with Thrift, should be:
#        raise TApplicationException(TApplicationException.MISSING_RESULT, "Static_call_me failed: unknown result");



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
                return self.call(procedure, values.named)
            except TTransportException:
                self.stop()
                self.start()
                return self.call(procedure, values.named)
            except HTTPException:
                self.stop()
                self.start()
                return self.call(procedure, values.named)
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

        self._http = (HTTPSConnection if self._ssl else HTTPConnection)(self._host, self._port) 
        self._processor = ThriftProcessor(self._interface)
        self._started = True

    def stop(self):
        if self._started:
            self._http.close()
            self._started = False
