# vim:ts=4:sts=4:sw=4:expandtab
"""Provider for the thrift protocol.
"""


__all__ = (
    'ThriftWriter',
)


from collections import Set
from types import ClassType, TypeType

from ..thrift.Thrift import TType, TProcessor, TMessageType, TApplicationException
from ..thrift.protocol.TProtocol import TProtocolBase
from ..thrift.server.TServer import TSimpleServer
from ..thrift.transport.TTransport import TServerTransportBase

from satori.objects import Object, Argument, Signature, DispatchOn, ArgumentError
from satori.ars.naming import NamedObject, NamingStyle
from satori.ars.model import Type, AtomicType, Boolean, Float, Int16, Int32, Int64, String, Void
from satori.ars.model import AtomicType, Boolean, Int8, Int16, Int32, Int64, Float, String, Void
from satori.ars.model import Field, ListType, MapType, SetType, Structure, TypeAlias
from satori.ars.model import Element, Parameter, Procedure, Contract
from satori.ars.api import Server
from satori.ars.common import ContractMixin, TopologicalWriter


class ThriftBase(Object):

    @Argument('style', type=NamingStyle, default=NamingStyle.IDENTIFIER)
    def __init__(self, style):
        self.style = style


class ThriftWriter(TopologicalWriter, ThriftBase):
    """An ARS Writer spitting out thrift IDL.
    """

    ATOMIC_NAMES = {
        Boolean: 'bool',
        Int8:    'byte',
        Int16:   'i16',
        Int32:   'i32',
        Int64:   'i64',
        Float:   'double',
        String:  'string',
        Void:    'void',
    }

    @DispatchOn(item=object)
    def _reference(self, item, target): # pylint: disable-msg=E0102
        raise RuntimeError("Unhandled Element type '{0}'".format(item.__class__.__name__))

    @DispatchOn(item=NamedObject)
    def _reference(self, item, target): # pylint: disable-msg=E0102
        target.write(self.style.format(item.name))

    @DispatchOn(item=AtomicType)
    def _reference(self, item, target): # pylint: disable-msg=E0102
        target.write(ThriftWriter.ATOMIC_NAMES[item])

    @DispatchOn(item=ListType)
    def _reference(self, item, target): # pylint: disable-msg=E0102
        target.write('list<')
        self._reference(item.element_type, target)
        target.write('>')

    @DispatchOn(item=MapType)
    def _reference(self, item, target): # pylint: disable-msg=E0102
        target.write('map<')
        self._reference(item.key_type, target)
        target.write(',')
        self._reference(item.value_type, target)
        target.write('>')

    @DispatchOn(item=SetType)
    def _reference(self, item, target): # pylint: disable-msg=E0102
        target.write('set<')
        self._reference(item.element_type, target)
        target.write('>')

    @DispatchOn(item=Element)
    def _write(self, item, target): # pylint: disable-msg=E0102
        raise ArgumentError("Unknown Element type '{0}'".format(item.__class__.__name__))

    @DispatchOn(item=(AtomicType,ListType,MapType,SetType,Field,Parameter,Procedure))
    def _write(self, item, target): # pylint: disable-msg=E0102
        pass

    @DispatchOn(item=TypeAlias)
    def _write(self, item, target): # pylint: disable-msg=E0102
        target.write('typedef ')
        self._reference(item.target_type, target)
        target.write(' ')
        self._reference(item, target)
        target.write('\n')

    @DispatchOn(item=Structure)
    def _write(self, item, target): # pylint: disable-msg=E0102
        target.write('struct ')
        self._reference(item, target)
        sep = ' {\n\t'
        ind = 1
        for field in item.fields:
            target.write('{0}{1}:'.format(sep, ind))
            if field.optional:
                target.write('optional ')
            self._reference(field.type, target)
            target.write(' ')
            self._reference(field, target)
            sep = '\n\t'
            ind += 1
        target.write('\n}\n')

    @DispatchOn(item=Contract)
    def _write(self, item, target): # pylint: disable-msg=E0102
        target.write('service ')
        self._reference(item, target)
        sep = ' {\n\t'
        for procedure in item.procedures:
            target.write(sep)
            self._reference(procedure.return_type, target)
            target.write(' ')
            self._reference(procedure, target)
            target.write('(')
            sep2 = ''
            ind = 1
            for parameter in procedure.parameters:
                target.write('{0}{1}:'.format(sep2, ind))
                if parameter.optional:
                    target.write('optional ')
                self._reference(parameter.type, target)
                target.write(' ')
                self._reference(parameter, target)
                if parameter.default is not None:
                    target.write(' = {0}'.format(parameter.default))
                sep2 = ', '
                ind += 1
            target.write(')')
            if procedure.error_type is not Void:
                target.write(' throws (1:')
                self._reference(procedure.error_type, target)
                target.write(' error)')
            sep = '\n\t'
        target.write('\n}\n')


class ThriftProcessor(ThriftBase, TProcessor):
    """ARS implementation of thrift.Thrift.TProcessor.
    """
    
    @Argument('contracts', type=Set)
    def __init__(self, contracts):
        self._procedures = {}
        for contract in contracts:
            for procedure in contract.procedures:
                pname = self.style.format(procedure.name)
                if pname not in self._procedures:
                    self._procedures[pname] = procedure
                elif self._procedures[pname] != procedure:
                    raise ArgumentError("Ambiguous procedure name: {0}".format(pname))

    ATOMIC_TYPE = {
        Boolean: TType.BOOL,
        Int16:   TType.I16,
        Int32:   TType.I32,
        Int64:   TType.I64,
        String:  TType.STRING,
        Void:    TType.VOID,
    }
    
    @DispatchOn(type_=AtomicType)
    def _ttype(self, type_):
        return ThriftProcessor.ATOMIC_TYPE[type_]
    
    @DispatchOn(type_=Structure)
    def _ttype(self, type_):
        return TType.STRUC

    @DispatchOn(type_=ListType)
    def _ttype(self, type_):
        return TType.LIST

    @DispatchOn(type_=MapType)
    def _ttype(self, type_):
        return TType.MAP

    @DispatchOn(type_=SetType)
    def _ttype(self, type_):
        return TType.SET

    ATOMIC_SEND = {
        Boolean: 'writeBool',
        Int16:   'writeI16',
        Int32:   'writeI32',
        Int64:   'writeI64',
        String:  'writeString',
    }

    @DispatchOn(type_=Type)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        raise RuntimeError("Unhandled ARS type: {0}".format(type_))

    @DispatchOn(type_=AtomicType)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        getattr(proto, ThriftProcessor.ATOMIC_SEND[type_])(value)
    
    @DispatchOn(type_=Structure)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        proto.writeStructBegin(self.style.format(type_.name))
        for index, field in enumerate(type_.fields):
            fname = self.style.format(field.name)
            fvalue = value.get(fname, None)
            if fvalue is not None:
                proto.writeFieldBegin(name, self._ttype(type_), findex+1)
                self._send(value, type_, proto)
                proto.writeFieldEnd()
        self.protocol.writeFieldStop()
        self.protocol.writeStructEnd()

    @DispatchOn(type_=ListType)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        proto.writeListBegin(self._ttype(type_.element_type), len(value))
        for item in value:
            self._send(item, type_.element_type, proto)
        proto.writeListEnd()

    @DispatchOn(type_=MapType)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        proto.writeMapBegin(self._ttype(type_.key_type), self._ttype(type_.value_type),
                            len(value))
        for key in value:
            self._send(key, type_.key_type, proto)
            self._send(value[key], type_.value_type_, proto)
        proto.writeMapEnd()

    @DispatchOn(type_=SetType)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        proto.writeSetBegin(self._ttype(type_.element_type), len(value))
        for item in value:
            self._send(item, type_.element_type, proto)
        proto.writeSetEnd()

    ATOMIC_RECV = {
        Boolean: 'readBool',
        Int16:   'readI16',
        Int32:   'readI32',
        Int64:   'readI64',
        String:  'readString',
    }

    @DispatchOn(type_=Type)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        raise RuntimeError("Unhandled ARS type: {0}".format(type_))

    @DispatchOn(type_=AtomicType)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        return getattr(proto, ThriftProcessor.ATOMIC_RECV[type_])()
    
    def _recvFields(self, fields, proto):
        value = {}
        proto.readStructBegin()
        while True:
            fname, ftype, findex = proto.readFieldBegin()
            if ftype == TType.STOP:
                break
            field = fields[findex-1]
            if fname is None:
                fname = self.style.format(field.name)
            elif fname != self.style.format(field.name):
                proto.skip(ftype)
                # TODO: warning: field name mismatch
            if ftype != self._ttype(field.type):
                proto.skip(ftype)
                # TODO: warning: field type mismatch
            value[fname] = self._recv(field.type, proto)
            proto.readFieldEnd()
        proto.readStructEnd()
        return value

    @DispatchOn(type_=Structure)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        value = self._recvFields(type_.fields, proto)
        for field in fields:
            fname = self.style.format(field.name)
            if fname in value:
                continue
            if not field.optional:
                raise Exception("No value for a mandatory component {0}".format(fname))
        return value

    @DispatchOn(type_=ListType)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        value = []
        itype, count = proto.readListBegin()
        if itype != self._ttype(type_.element_type):
            raise Exception("Element type mismatch")
        for index in xrange(count):
            value.append(self._recv(type_.element_type, proto))
        proto.readListEnd()
        return value

    @DispatchOn(type_=MapType)
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
        proto.readListEnd()
        return value

    @DispatchOn(type_=SetType)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        value = set()
        itype, count = proto.readSetBegin()
        if itype != self._ttype(type_.element_type):
            raise Exception("Element type mismatch")
        for index in xrange(count):
            value.add(self._recv(type_.element_type, proto))
        proto.readSetEnd()
        return value
    
    def process(self, iproto, oproto):
        """Processes a single client request.
        """
        pname, _, seqid = iproto.readMessageBegin()
        try:
            # find the procedure to call
            try:
                procedure = self._procedures[pname] # TApplicationException.UNKNOWN_METHOD
            except KeyError:
                iproto.skip(TType.STRUCT)
                raise TApplicationException(TApplicationException.UNKNOWN_METHOD,
                    "Unknown method '{0}'".format(pname))
            # parse and check arguments
            try:
                signature = Signature.infer(procedure.implementation)
                arguments = self._recvFields(procedure.parameters, iproto)
                iproto.readMessageEnd()
                values = signature.Values(**arguments)
            except ArgumentError as ex:
                raise TApplicationException(TApplicationException.MISSING_RESULT,
                    "Error processing arguments: " + ex.message)
            # call the registered implementation
            try:
                result_value = values.call(procedure.implementation)
                result_type = procedure.return_type
                result_index = 0
                result_name = 'success'
            except Exception as ex:
                # handle "expected" (registered) exceptions
                try:
                    result_value = procedure.error_transform(ex)
                    result_type = procedure.error_type
                    result_index = 1
                    result_name = 'error'
                except:
                    raise TApplicationException(TApplicationException.MISSING_RESULT,
                        "Error processing exception: " + ex.message)
            # send the reply
            try:
                oproto.writeMessageBegin(pname, TMessageType.REPLY, seqid)
                oproto.writeStructBegin(pname + '_result')
                oproto.writeFieldBegin(result_name, self._ttype(result_type), result_index)
                self._send(result_value, result_type, oproto)
                oproto.writeFieldEnd()
                oproto.writeFieldStop()
                oproto.writeStructEnd()
                oproto.writeMessageEnd()
            except Exception as ex:
                raise TApplicationException(TApplicationException.MISSING_RESULT,
                    "Error processing result: " + ex.message)
        except TApplicationException as ex:
            # handle protocol errors
            oproto.writeMessageBegin(pname, TMessageType.EXCEPTION, seqid)
            ex.write(oproto)
            oproto.writeMessageEnd()
        finally:
            oproto.trans.flush()

class ThriftServer(ContractMixin, Server):
    
    @Argument('server_type', type=(ClassType, TypeType), default=TSimpleServer)
    @Argument('transport', type=TServerTransportBase)
    @Argument('changeContracts', fixed=True)
    def __init__(self, server_type, transport):
        self._server_type = server_type
        self._transport = transport
    
    def run(self):
        processor = ThriftProcessor(self.contracts)
        server = self._server_type(processor, self._transport)
        return server.serve()
