# vim:ts=4:sts=4:sw=4:expandtab
"""Processor for the thrift protocol.
"""

import traceback

from thrift.Thrift import TType, TProcessor, TMessageType, TApplicationException
from thrift.transport.TTransport import TFramedTransport

from satori.objects import Argument, DispatchOn, Signature, Namespace
from satori.ars.model import *
from satori.ars.server import server_info
try:
    from thrift.protocol import fastbinary
except:
    fastbinary = None

class ThriftProcessor(TProcessor):
    """ARS implementation of thrift.Thrift.TProcessor.
    """
    
    @Argument('interface', type=ArsInterface)
    def __init__(self, interface):
        self._procedures = ArsNamedTuple()
        self._typeargs_map = {}
        for service in interface.services:
            self._procedures.extend(service.procedures)
        self.seqid = 0

    ATOMIC_TYPE = {
        ArsBoolean: TType.BOOL,
        ArsInt8:    TType.BYTE,
        ArsInt16:   TType.I16,
        ArsInt32:   TType.I32,
        ArsInt64:   TType.I64,
        ArsFloat:   TType.DOUBLE,
        ArsString:  TType.STRING,
        ArsVoid:    TType.VOID,
    }
    
    @DispatchOn(type_=ArsAtomicType)
    def _ttype(self, type_):
        return ThriftProcessor.ATOMIC_TYPE[type_]
    
    @DispatchOn(type_=ArsStructure)
    def _ttype(self, type_):
        return TType.STRUCT

    @DispatchOn(type_=ArsList)
    def _ttype(self, type_):
        return TType.LIST

    @DispatchOn(type_=ArsMap)
    def _ttype(self, type_):
        return TType.MAP

    @DispatchOn(type_=ArsSet)
    def _ttype(self, type_):
        return TType.SET
    
    @DispatchOn(type_=ArsTypeAlias)
    def _ttype(self, type_):
        return self._ttype(type_.target_type)

    ATOMIC_SEND = {
        ArsBoolean: 'writeBool',
        ArsInt8:    'writeByte',
        ArsInt16:   'writeI16',
        ArsInt32:   'writeI32',
        ArsInt64:   'writeI64',
        ArsFloat:   'writeDouble',
        ArsString:  'writeString',
    }

    @DispatchOn(type_=ArsType)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        raise RuntimeError("Unhandled ARS type: {0}".format(type_))

    @DispatchOn(type_=ArsAtomicType)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        if type_ != ArsVoid:
            getattr(proto, ThriftProcessor.ATOMIC_SEND[type_])(value)
    
    @DispatchOn(type_=ArsTypeAlias)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        return self._send(value, type_.target_type, proto)

    @DispatchOn(type_=ArsStructure)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        proto.writeStructBegin(type_.name)
        for index, field in enumerate(type_.fields):
            fvalue = value.get(field.name, None)
            if fvalue is not None:
                proto.writeFieldBegin(field.name, self._ttype(field.type), index + type_.base_index)
                self._send(fvalue, field.type, proto)
                proto.writeFieldEnd()
        proto.writeFieldStop()
        proto.writeStructEnd()

    @DispatchOn(type_=ArsList)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        proto.writeListBegin(self._ttype(type_.element_type), len(value))
        for item in value:
            self._send(item, type_.element_type, proto)
        proto.writeListEnd()

    @DispatchOn(type_=ArsMap)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        proto.writeMapBegin(self._ttype(type_.key_type), self._ttype(type_.value_type),
                            len(value))
        for key in value:
            self._send(key, type_.key_type, proto)
            self._send(value[key], type_.value_type, proto)
        proto.writeMapEnd()

    @DispatchOn(type_=ArsSet)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        proto.writeSetBegin(self._ttype(type_.element_type), len(value))
        for item in value:
            self._send(item, type_.element_type, proto)
        proto.writeSetEnd()
    
    ATOMIC_RECV = {
        ArsBoolean: 'readBool',
        ArsInt8:    'readByte',
        ArsInt16:   'readI16',
        ArsInt32:   'readI32',
        ArsInt64:   'readI64',
        ArsFloat:   'readDouble',
        ArsString:  'readString',
    }

    @DispatchOn(type_=ArsType)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        raise RuntimeError("Unhandled ARS type: {0}".format(type_))

    @DispatchOn(type_=ArsAtomicType)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        if type_ == ArsVoid:
            return None
        else:
            return getattr(proto, ThriftProcessor.ATOMIC_RECV[type_])()
    
    @DispatchOn(type_=ArsTypeAlias)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        return self._recv(type_.target_type, proto)
    
    @DispatchOn(type_=ArsStructure)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        value = {}
        proto.readStructBegin()
        while True:
            fname, ftype, findex = proto.readFieldBegin()
            if ftype == TType.STOP:
                break
            field = type_.fields[findex - type_.base_index]
            if fname is None:
                fname = field.name
            elif fname != field.name:
                proto.skip(ftype)
                # TODO: warning: field name mismatch
            if ftype != self._ttype(field.type):
                proto.skip(ftype)
                # TODO: warning: field type mismatch
            value[field.name] = self._recv(field.type, proto)
            proto.readFieldEnd()
        proto.readStructEnd()
        for field in type_.fields:
            if field.name in value:
                continue
            if not field.optional:
                raise Exception("No value for a mandatory field {0}".format(field.name))
        return value

    @DispatchOn(type_=ArsList)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        value = []
        itype, count = proto.readListBegin()
        if itype != self._ttype(type_.element_type):
            raise Exception("Element type mismatch")
        for index in xrange(count):
            value.append(self._recv(type_.element_type, proto))
        proto.readListEnd()
        return value

    @DispatchOn(type_=ArsMap)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        value = {}
        ktype, vtype, count = proto.readMapBegin()
        if ktype != self._ttype(type_.key_type):
            raise Exception("Key type mismatch")
        if vtype != self._ttype(type_.value_type):
            raise Exception("Value type mismatch")
        for index in xrange(count):
            kvalue = self._recv(type_.key_type, proto)
            vvalue = self._recv(type_.value_type, proto)
            value[kvalue] = vvalue
        proto.readMapEnd()
        return value

    @DispatchOn(type_=ArsSet)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        value = set()
        itype, count = proto.readSetBegin()
        if itype != self._ttype(type_.element_type):
            raise Exception("Element type mismatch")
        for index in xrange(count):
            value.add(self._recv(type_.element_type, proto))
        proto.readSetEnd()
        return value

    @DispatchOn(type_=ArsAtomicType)
    def _typeargs(self, type_):
        return (self.ATOMIC_TYPE[type_], None)

    @DispatchOn(type_=ArsList)
    def _typeargs(self, type_):
        return (TType.LIST, self.typeargs(type_.element_type))

    @DispatchOn(type_=ArsSet)
    def _typeargs(self, type_):
        return (TType.SET, self.typeargs(type_.element_type))

    @DispatchOn(type_=ArsMap)
    def _typeargs(self, type_):
        (ktype, kargs) = self.typeargs(type_.key_type)
        (vtype, vargs) = self.typeargs(type_.value_type)

        return (TType.MAP, (ktype, kargs, vtype, vargs))

    @DispatchOn(type_=ArsTypeAlias)
    def _typeargs(self, type_):
        return self.typeargs(type_.target_type)

    @DispatchOn(type_=ArsStructure)
    def _typeargs(self, type_):
        fields = []
        for i in range(type_.base_index):
        	fields.append(None)

        for (i, field) in enumerate(type_.fields):
        	(ftype, fargs) = self.typeargs(field.type)
        	fields.append((i + type_.base_index, ftype, field.name, fargs, None))

        return (TType.STRUCT, (Namespace, tuple(fields)))

    def typeargs(self, type_):
        if type_ not in self._typeargs_map:
        	self._typeargs_map[type_] = self._typeargs(type_)
        return self._typeargs_map[type_]

    def send_struct(self, value, struct, oproto):
        if fastbinary is not None:
        	oproto.trans.write(fastbinary.encode_binary(value, self.typeargs(struct)[1]))
        else:
        	self._send(value, struct, oproto)

    def recv_struct(self, struct, iproto):
        if fastbinary is not None:
        	ret = Namespace()
        	fastbinary.decode_binary(ret, iproto.trans, self.typeargs(struct)[1])
        	return ret
        else:
        	return self._recv(struct, iproto)

    def process(self, iproto, oproto):
        """Processes a single client request.
        """
        pname, _, seqid = iproto.readMessageBegin()
#        perf.begin('process')
        try:
            # find the procedure to call
            if not pname in self._procedures:
                iproto.skip(TType.STRUCT)
                iproto.readMessageEnd()
                raise TApplicationException(TApplicationException.UNKNOWN_METHOD,
                    "Unknown method '{0}'".format(pname))

            procedure = self._procedures[pname] # TApplicationException.UNKNOWN_METHOD

            # parse arguments
#            perf.begin('recv')
            arguments = self.recv_struct(procedure.parameters_struct, iproto)
            iproto.readMessageEnd()
#            perf.end('recv')
            
            # call the registered implementation
#            perf.begin('call')

            server_info.client_ip = None
            server_info.client_port = None
            try:
                if isinstance(iproto.trans, TFramedTransport):
                	info = iproto.trans._TFramedTransport__trans.handle.getpeername()
                else:
                    info = iproto.trans.handle.getpeername()
                server_info.client_ip = str(info[0])
                server_info.client_port = int(info[1])
            except:
                pass
            print 'Server serving client: ', server_info.client_ip, ':', server_info.client_port, ',', pname
            result = Namespace()
            try:
                result['result'] = procedure.implementation(**arguments)
            except Exception as ex:
                traceback.print_exc()
                raise TApplicationException(TApplicationException.UNKNOWN,
                    "Exception: " + ex.message)
#            perf.end('call')

            # send the reply
#            perf.begin('send')
            oproto.writeMessageBegin(pname, TMessageType.REPLY, seqid)
            self.send_struct(result, procedure.results_struct, oproto)
            oproto.writeMessageEnd()
#            perf.end('send')
        except TApplicationException as ex:
            # handle protocol errors
#            perf.begin('except')
            oproto.writeMessageBegin(pname, TMessageType.EXCEPTION, seqid)
            ex.write(oproto)
            oproto.writeMessageEnd()
#            perf.end('except')
        finally:
#            perf.begin('flush')
            oproto.trans.flush()
#            perf.end('flush')
#            perf.end('process')

    def call(self, procedure, args, iproto, oproto):
#        perf.begin('call')
        if isinstance(procedure, str):
            try:
                procedure = self._procedures[procedure]
            except KeyError:
                raise TApplicationException(TApplicationException.UNKNOWN_METHOD,
                    "Unknown method '{0}'".format(name))
        
#        perf.begin('send')
        oproto.writeMessageBegin(procedure.name, TMessageType.CALL, self.seqid)
        self.seqid = self.seqid + 1
        self.send_struct(Namespace(args), procedure.parameters_struct, oproto)
        oproto.writeMessageEnd()
        oproto.trans.flush()
#        perf.end('send')

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
        result = self.recv_struct(procedure.results_struct, iproto)
        iproto.readMessageEnd()
#        perf.end('recv')
#        perf.end('call')

        if 'result' in result:
            return result['result']
        if 'error' in result:
            raise result['error']
        return None
#       previous line not compatible with Thrift, should be:
#        raise TApplicationException(TApplicationException.MISSING_RESULT, "Static_call_me failed: unknown result");

