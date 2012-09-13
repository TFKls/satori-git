import logging

from thrift.Thrift import TType, TProcessor, TMessageType, TApplicationException
from thrift.protocol import fastbinary
from thrift.protocol.TBinaryProtocol import TBinaryProtocol
from thrift.transport.TTransport import TMemoryBuffer, TFramedTransport

from django.http import HttpResponse, HttpResponseNotAllowed

from satori.ars.model import *
from satori.ars.server import server_info
from satori.core.api import ars_interface

ATOMIC_TYPE = {
    ArsBinary:  TType.STRING,
    ArsBoolean: TType.BOOL,
    ArsInt8:    TType.BYTE,
    ArsInt16:   TType.I16,
    ArsInt32:   TType.I32,
    ArsInt64:   TType.I64,
    ArsFloat:   TType.DOUBLE,
    ArsString:  TType.STRING,
    ArsVoid:    TType.VOID,
}

def make_ttype(type_):
    if isinstance(type_, ArsAtomicType):
        return (ATOMIC_TYPE[type_], None)
    elif isinstance(type_, ArsList):
        return (TType.LIST, make_ttype(type_.element_type))
    elif isinstance(type_, ArsSet):
        return (TType.SET, make_ttype(type_.element_type))
    elif isinstance(type_, ArsMap):
        (ktype, kargs) = make_ttype(type_.key_type)
        (vtype, vargs) = make_ttype(type_.value_type)

        return (TType.MAP, (ktype, kargs, vtype, vargs))
    elif isinstance(type_, ArsTypeAlias):
        return make_ttype(type_.target_type)
    elif isinstance(type_, ArsStructure):
        fields = []
        for i in range(type_.base_index):
            fields.append(None)

        for (i, field) in enumerate(type_.fields):
            (ftype, fargs) = make_ttype(field.type)
            fields.append((i + type_.base_index, ftype, field.name, fargs, None))

        return (TType.STRUCT, (type_.get_class(), tuple(fields)))

parameters_ttypes = {}
result_ttypes = {}
procedures = {}

for service in ars_interface.services:
    for procedure in service.procedures:
        procedures[procedure.name] = procedure
        parameters_ttypes[procedure.name] = make_ttype(procedure.parameters_struct)[1]
        result_ttypes[procedure.name] = make_ttype(procedure.results_struct)[1]

def http_handler(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['GET', 'PUT'])

    server_info.client_ip = request.META['REMOTE_ADDR']
    if server_info.client_ip[0:7] == '::ffff:':
        server_info.client_ip = server_info.client_ip[7:]
    server_info.client_port = None

    itrans = TMemoryBuffer(request.body)
    otrans = TMemoryBuffer()
    iproto = TBinaryProtocol(itrans)
    oproto = TBinaryProtocol(otrans)
    thrift_handler(iproto, oproto)
    return HttpResponse(otrans.getvalue(), content_type="application/x-thrift")

class ThriftProcessor(TProcessor):
    def process(self, iproto, oproto):
        try:
            if isinstance(iproto.trans, TFramedTransport):
                info = iproto.trans._TFramedTransport__trans.handle.getpeername()
            else:
                info = iproto.trans.handle.getpeername()
            server_info.client_ip = str(info[0])
            if server_info.client_ip[0:7] == '::ffff:':
                server_info.client_ip = server_info.client_ip[7:]
            server_info.client_port = int(info[1])
        except:
            server_info.client_ip = None
            server_info.client_port = None

        thrift_handler(iproto, oproto)

def thrift_handler(iproto, oproto):
    pname, _, seqid = iproto.readMessageBegin()
    try:
        if pname not in procedures:
            iproto.skip(TType.STRUCT)
            iproto.readMessageEnd()
            raise TApplicationException(TApplicationException.UNKNOWN_METHOD,
                "Unknown method '{0}'".format(pname))

        procedure = procedures[pname]

        logging.debug('Server serving client: %s:%s, %s', server_info.client_ip, server_info.client_port, pname)

        # parse arguments
        parameters = procedure.parameters_struct.get_class()()
        fastbinary.decode_binary(parameters, iproto.trans, parameters_ttypes[pname])
        iproto.readMessageEnd()

        # call the registered implementation
        result = procedure_handler(procedure, parameters)

        # send the reply
        oproto.writeMessageBegin(pname, TMessageType.REPLY, seqid)
        oproto.trans.write(fastbinary.encode_binary(result, result_ttypes[pname]))
        oproto.writeMessageEnd()
    except TApplicationException as ex:
        oproto.writeMessageBegin(pname, TMessageType.EXCEPTION, seqid)
        ex.write(oproto)
        oproto.writeMessageEnd()
    finally:
        oproto.trans.flush()

def procedure_handler(procedure, parameters):
    result = procedure.results_struct.get_class()()
    try:
        args = {}
        for parameter in procedure.parameters:
            if getattr(parameters, parameter.name) is not None:
                args[parameter.name] = getattr(parameters, parameter.name)
        result.result = procedure.implementation(**args)
    except Exception as ex:
        logging.exception('Exception in procedure: %s:%s, %s', server_info.client_ip, server_info.client_port, procedure.name)
        handled = False
        for field in procedure.results_struct.fields:
            if (field.name != 'result') and isinstance(ex, field.type.get_class()):
                setattr(result, field.name, ex)
                handled = True
                break
        if not handled:
            raise TApplicationException(TApplicationException.UNKNOWN, 'Unknown exception in procedure')
    return result
