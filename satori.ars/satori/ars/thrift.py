# vim:ts=4:sts=4:sw=4:expandtab
"""Provider for the thrift protocol.
"""


__all__ = (
    'ThriftWriter',
    'ThriftServer',
    'ThriftReader',
    'ThriftClient',
)


from collections import Set
from StringIO import StringIO
import traceback
from types import ClassType, TypeType, FunctionType
import threading

from pyparsing import Forward, Group, Literal, Optional, Regex, StringEnd
from pyparsing import Suppress, ZeroOrMore;
from pyparsing import cStyleComment, dblSlashComment, pythonStyleComment
from pyparsing import dblQuotedString, sglQuotedString, removeQuotes

from ..thrift.Thrift import TType, TProcessor, TMessageType, TApplicationException
from ..thrift.protocol.TProtocol import TProtocolBase
from ..thrift.server.TServer import TThreadedServer
from ..thrift.transport.TTransport import TServerTransportBase, TTransportBase
from ..thrift.protocol.TBinaryProtocol import TBinaryProtocol

from satori.objects import Object, Argument, ArgumentMode, Signature, DispatchOn, ArgumentError
from satori.ars.model import Type, NamedType, AtomicType, Boolean, Float, Int8, Int16, Int32, Int64, String, Void
from satori.ars.model import Field, ListType, MapType, SetType, Structure, Exception as ArsException, TypeAlias
from satori.ars.model import Element, NamedElement, Parameter, Procedure, Contract, NamedTuple
from satori.ars.api import Server, Reader, Client
from satori.ars.common import TopologicalWriter

import perf
import sys


class ThriftWriter(TopologicalWriter):
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

    @DispatchOn(item=Element)
    def _reference(self, item, target): # pylint: disable-msg=E0102
        raise RuntimeError("Unhandled Element type '{0}'".format(item.__class__.__name__))

    @DispatchOn(item=NamedElement)
    def _reference(self, item, target): # pylint: disable-msg=E0102
        target.write(item.name)

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

    @DispatchOn(item=Element)
    def _sortkey(self, item): # pylint: disable-msg=E0102
        raise ArgumentError("Unknown Element type '{0}'".format(item.__class__.__name__))

    @DispatchOn(item=(AtomicType,ListType,MapType,SetType,Field,Parameter,Procedure))
    def _write(self, item, target): # pylint: disable-msg=E0102
        pass

    @DispatchOn(item=(AtomicType,ListType,MapType,SetType,Field,Parameter,Procedure))
    def _sortkey(self, item): # pylint: disable-msg=E0102
        pass 

    def _sortkey(self, item):
        target = StringIO()
        self._reference(item, target)
        return str(target)

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
        target.write(' {')
        sep = '\n\t'
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
        if item.base:
        	target.write(' extends ')
        	self._reference(item.base, target)
        target.write(' {')
        sep = '\n\t'
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
            if procedure.exception_types:
                target.write(' throws (')
                sep2 = ''
                ind = 1
                for exception_type in procedure.exception_types:
                    target.write('{0}{1}:'.format(sep2, ind))
                    self._reference(procedure.error_type, target)
                    target.write(' error')
                    sep2 = ', '
                    ind += 1
                target.write(')')
            sep = '\n\t'
        target.write('\n}\n')

class ThriftProcessor(TProcessor):
    """ARS implementation of thrift.Thrift.TProcessor.
    """
    
    @Argument('contracts', type=NamedTuple)
    def __init__(self, contracts):
        self._procedures = {}
        for contract in contracts:
            for procedure in contract.procedures:
                if procedure.name not in self._procedures:
                    self._procedures[procedure.name] = procedure
                elif self._procedures[procedure.name] != procedure:
                    raise ArgumentError("Ambiguous procedure name: {0}".format(procedure.name))
        self.seqid = 0

    ATOMIC_TYPE = {
        Boolean: TType.BOOL,
        Int8:    TType.BYTE,
        Int16:   TType.I16,
        Int32:   TType.I32,
        Int64:   TType.I64,
        Float:   TType.DOUBLE,
        String:  TType.STRING,
        Void:    TType.VOID,
    }
    
    @DispatchOn(type_=AtomicType)
    def _ttype(self, type_):
        return ThriftProcessor.ATOMIC_TYPE[type_]
    
    @DispatchOn(type_=Structure)
    def _ttype(self, type_):
        return TType.STRUCT

    @DispatchOn(type_=ListType)
    def _ttype(self, type_):
        return TType.LIST

    @DispatchOn(type_=MapType)
    def _ttype(self, type_):
        return TType.MAP

    @DispatchOn(type_=SetType)
    def _ttype(self, type_):
        return TType.SET
    
    @DispatchOn(type_=TypeAlias)
    def _ttype(self, type_):
        return self._ttype(type_.target_type)

    ATOMIC_SEND = {
        Boolean: 'writeBool',
        Int8:    'writeByte',
        Int16:   'writeI16',
        Int32:   'writeI32',
        Int64:   'writeI64',
        Float:   'writeDouble',
        String:  'writeString',
    }

    @DispatchOn(type_=Type)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        raise RuntimeError("Unhandled ARS type: {0}".format(type_))

    @DispatchOn(type_=AtomicType)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        if type_ != Void:
            getattr(proto, ThriftProcessor.ATOMIC_SEND[type_])(value)
    
    @DispatchOn(type_=TypeAlias)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        return self._send(value, type_.target_type, proto)

    @DispatchOn(type_=Structure)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        proto.writeStructBegin(type_.name)
        for index, field in enumerate(type_.fields):
            fvalue = value.get(field.name, None)
            if fvalue is not None:
                proto.writeFieldBegin(field.name, self._ttype(field.type), index + type_.base)
                self._send(fvalue, field.type, proto)
                proto.writeFieldEnd()
        proto.writeFieldStop()
        proto.writeStructEnd()

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
            self._send(value[key], type_.value_type, proto)
        proto.writeMapEnd()

    @DispatchOn(type_=SetType)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        proto.writeSetBegin(self._ttype(type_.element_type), len(value))
        for item in value:
            self._send(item, type_.element_type, proto)
        proto.writeSetEnd()
    
    ATOMIC_RECV = {
        Boolean: 'readBool',
        Int8:    'readByte',
        Int16:   'readI16',
        Int32:   'readI32',
        Int64:   'readI64',
        Float:   'readDouble',
        String:  'readString',
    }

    @DispatchOn(type_=Type)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        raise RuntimeError("Unhandled ARS type: {0}".format(type_))

    @DispatchOn(type_=AtomicType)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        if type_ == Void:
            return None
        else:
            return getattr(proto, ThriftProcessor.ATOMIC_RECV[type_])()
    
    @DispatchOn(type_=TypeAlias)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        return self._recv(type_.target_type, proto)
    
    def _recvFields(self, fields, proto):
        value = {}
        proto.readStructBegin()
        while True:
            fname, ftype, findex = proto.readFieldBegin()
            if ftype == TType.STOP:
                break
            field = fields[findex]
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
        return value

    @DispatchOn(type_=Structure)
    def _recv(self, type_, proto): # pylint: disable-msg=E0102
        value = {}
        proto.readStructBegin()
        while True:
            fname, ftype, findex = proto.readFieldBegin()
            if ftype == TType.STOP:
                break
            field = type_.fields[findex - type_.base]
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
        proto.readMapEnd()
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
        perf.begin('process')
        print pname
        try:
            # find the procedure to call
            if not pname in self._procedures:
                iproto.skip(TType.STRUCT)
                iproto.readMessageEnd()
                raise TApplicationException(TApplicationException.UNKNOWN_METHOD,
                    "Unknown method '{0}'".format(pname))

            procedure = self._procedures[pname] # TApplicationException.UNKNOWN_METHOD

            # parse arguments
            perf.begin('recv')
            arguments = self._recv(procedure.parameters_struct, iproto)
            iproto.readMessageEnd()
            perf.end('recv')
            
            # call the registered implementation
            perf.begin('call')
            result = {}
            try:
                result['result'] = procedure.implementation(**arguments)
            except Exception as ex:
                traceback.print_exc()
                raise TApplicationException(TApplicationException.UNKNOWN,
                    "Exception: " + ex.message)
            perf.end('call')

            # send the reply
            perf.begin('send')
            oproto.writeMessageBegin(pname, TMessageType.REPLY, seqid)
            self._send(result, procedure.results_struct, oproto)
            oproto.writeMessageEnd()
            perf.end('send')
        except TApplicationException as ex:
            # handle protocol errors
            perf.begin('except')
            oproto.writeMessageBegin(pname, TMessageType.EXCEPTION, seqid)
            ex.write(oproto)
            oproto.writeMessageEnd()
            perf.end('except')
        finally:
            perf.begin('flush')
            oproto.trans.flush()
            perf.end('flush')
            perf.end('process')

    def call(self, procedure, args, iproto, oproto):
        perf.begin('call')
        if isinstance(procedure, str):
            try:
                procedure = self._procedures[procedure]
            except KeyError:
                raise TApplicationException(TApplicationException.UNKNOWN_METHOD,
                    "Unknown method '{0}'".format(name))
        
        perf.begin('send')
        oproto.writeMessageBegin(procedure.name, TMessageType.CALL, self.seqid)
        self.seqid = self.seqid + 1
        self._send(args, procedure.parameters_struct, oproto)
        oproto.writeMessageEnd()
        oproto.trans.flush()
        perf.end('send')

        perf.begin('wait')
        (fname, mtype, rseqid) = iproto.readMessageBegin()
        perf.end('wait')

        perf.begin('recv')
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iproto)
            iproto.readMessageEnd()
            x.args = (x.message,)
            raise x
        result = self._recv(procedure.results_struct, iproto)
        iproto.readMessageEnd()
        perf.end('recv')
        perf.end('call')

        if 'result' in result:
        	return result['result']
        if 'error' in result:
        	raise result['error']
        return None
#       previous line not compatible with Thrift, should be:
#        raise TApplicationException(TApplicationException.MISSING_RESULT, "Static_call_me failed: unknown result");


class ThriftServer(Server):
    
    @Argument('server_type', type=(ClassType, TypeType), default=TThreadedServer)
    @Argument('transport', type=TServerTransportBase)
    @Argument('contracts', type=NamedTuple)
    def __init__(self, server_type, transport, contracts):
        super(ThriftServer, self).__init__()
        self._server_type = server_type
        self._transport = transport
        self.contracts = contracts
    
    def run(self):
        idl_proc = Procedure(return_type=String, name='Server_getIDL')
        idl_cont = Contract(name='Server')
        idl_cont.add_procedure(idl_proc)
        self.contracts.append(idl_cont)
        writer = ThriftWriter()
        idl = StringIO()
        writer.writeTo(self.contracts, idl)
        idl = idl.getvalue()
        def do_idl():
            perf.clear('process')
            perf.clear('call')
            perf.clear('delete')
            return idl
        idl_proc.implementation = do_idl
#        idl_proc.implementation = lambda: idl
        processor = ThriftProcessor(self.contracts)
        server = self._server_type(processor, self._transport)
        return server.serve()


class ThriftClient(threading.local):
    @Argument('contracts', type=NamedTuple)
    @Argument('transport_factory', type=FunctionType)
    def __init__(self, contracts, transport_factory):
        super(ThriftClient, self).__init__()
        self._contracts = contracts
        self._transport_factory = transport_factory
        self._started = False

    def _wrap(self, procedure):
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
            return self._processor.call(procedure, values.named, self._protocol, self._protocol)

        proc.func_name = procedure.name
        return proc

    def wrap_all(self):
        for contract in self._contracts:
            for procedure in contract.procedures:
                procedure.implementation = self._wrap(procedure)
        return self._contracts

    def unwrap_all(self):
        for contract in self._contracts:
            for procedure in contract.procedures:
                procedure.implementation = None
        return self._contracts

    def start(self):
        if self._started:
        	self.stop()
        	
        self._transport = self._transport_factory()
        self._transport.open()
        self._protocol = TBinaryProtocol(self._transport)
        self._processor = ThriftProcessor(self._contracts)
        self._started = True

    def stop(self):
        if self._started:
            self._transport.close()
            self._started = False


def BootstrapThriftClient(transport_factory):
    contracts = NamedTuple()

    idl_proc = Procedure(return_type=String, name='Server_getIDL')
    idl_cont = Contract(name='Server')
    idl_cont.add_procedure(idl_proc)
    contracts.append(idl_cont)

    bootstrap_client = ThriftClient(contracts, transport_factory)
    bootstrap_client.wrap_all()
    idl = idl_proc.implementation()
    bootstrap_client.stop()
    
    import satori.core.setup
    from satori.ars import wrapper
    import satori.core.api
    contracts.extend(wrapper.generate_contracts())
    writer = ThriftWriter()
    idl2 = StringIO()
    writer.writeTo(contracts, idl2)
    idl2 = idl2.getvalue()
    first = "\n".join(sorted(idl.split("\n")))
    second = "\n".join(sorted(idl2.split("\n")))

    if True:# first != second:
        print "Server and client api mismatch. Using server version."
        idl_reader = ThriftReader()
        idl_io = StringIO(idl)
        contracts = idl_reader.readFrom(idl_io)

    client = ThriftClient(contracts, transport_factory)

    return client


class ThriftReader(Reader):
    def setType(self, name, type):
        self._types[name] = type
        return [type]
    def getType(self, name):
        if isinstance(name,Type):
            return name
        return self._types[name]
    def clearType(self):
        self._types = {}
        self.setType('bool', Boolean)
        self.setType('byte', Int8)
        self.setType('i16', Int16)
        self.setType('i32', Int32)
        self.setType('i64', Int64)
        self.setType('double', Float)
        self.setType('string', String)
        self.setType('void', Void)
        self.setType('binary', String)
        self.setType('slist', String)

    def setConst(self, name, const):
        self._consts[name] = const
        return [const]
    def getConst(self, name):
        return self._consts[name]
    def clearConst(self):
        self._consts = {}

    def setService(self, name, service):
        self._services.append(service)
        return [service]
    def getService(self, name):
        return self._services[name]
    def clearService(self):
        self._services = NamedTuple()

    def __init__(self):
        super(ThriftReader, self).__init__()
        class Junk(Suppress):
            def __init__(self, str):
                super(Junk, self).__init__(Literal(str))

        idlListSeparator   =  Suppress(Optional(Regex('[,;]')))

        idlSTIdentifier    =  Regex('[A-Za-z_][-A-Za-z0-9._]*')

        idlIdentifier      =  Regex('[A-Za-z_][A-Za-z0-9._]*')

        idlLiteral         =  (dblQuotedString ^ sglQuotedString)
        idlLiteral.setParseAction(lambda s,l,t: [str(t[0][1:-1])])

        idlConstValue      =  Forward()

        idlConstMap        =  Junk('{') + Group(ZeroOrMore(Group(
                                  idlConstValue.setResultsName('key') +
                                  Junk(':') +
                                  idlConstValue.setResultsName('value')
                              ) + idlListSeparator)) + Junk('}')
        idlConstMap.setParseAction(lambda s,l,t:
            [dict([[tt['key'], tt['value']] for tt in t[0]])]
        )

        idlConstList       =  Junk('[') + Group(ZeroOrMore(Group(
                                  idlConstValue.setResultsName('element')
                              ) + idlListSeparator)) + Junk(']')
        idlConstList.setParseAction(lambda s,l,t:
            [[tt['element'] for tt in t[0]]]
        )

        idlIntConstant     =  Regex('[+-]?[0-9]+') ^ \
                              Regex('[+-]?0[xX][0-9A-Fa-f]+')
        idlIntConstant.setParseAction(lambda s,l,t: [int(t[0], 0)])

        idlDoubleConstant  =  Regex('[+-]?[0-9]+(?:\.[0-9]+)?(?:[Ee][+-]?[0-9]+)?')
        idlDoubleConstant.setParseAction(lambda s,l,t: [float(t[0])])

        idlConstValue      << (idlIntConstant ^ idlDoubleConstant ^ idlLiteral ^ \
                              idlIdentifier.copy().setParseAction(lambda s,l,t:
                                  [self.getConst(t[0])]
                              ) ^ idlConstList ^ idlConstMap)

        idlCppType         =  Junk('cpp_type') + idlLiteral

        idlAnnotation      =  Junk('(') + Group(ZeroOrMore(Group(
                                  idlIdentifier.setResultsName('key') +
                                  Junk('=') +
                                  idlLiteral.setResultsName('value')
                              ) + idlListSeparator)) + Junk(')')
        idlAnnotation.setParseAction(lambda s,l,t:
            [dict([[tt['key'], tt['value']] for tt in t[0]])]
        )

        idlFieldType       =  Forward()

        idlListType        =  Junk('list') + Junk('<') + \
                              idlFieldType.setResultsName('base') + \
                              Junk('>') + Optional(idlCppType)
        idlListType.setParseAction(lambda s,l,t:
            [ListType(t['base'])]
        )

        idlSetType         =  Junk('set') + Optional(idlCppType) + Junk('<') + \
                              idlFieldType.setResultsName('base') + \
                              Junk('>')
        idlSetType.setParseAction(lambda s,l,t:
            [SetType(t['base'])]
        )

        idlMapType         =  Junk('map') + Optional(idlCppType) + Junk('<') + \
                              idlFieldType.setResultsName('basek') + \
                              Junk(',') + \
                              idlFieldType.setResultsName('basev') + \
                              Junk('>')
        idlMapType.setParseAction(lambda s,l,t:
            [MapType(t['basek'], t['basev'])]
        )

        idlContainerType   =  (idlMapType ^ idlSetType ^ idlListType) + \
                              Suppress(Optional(idlAnnotation))

        idlBaseType        =  (Literal('bool') ^ Literal('byte') ^ \
                              Literal('i16') ^ Literal('i32') ^ \
                              Literal('i64') ^ Literal('double') ^ \
                              Literal('string') ^ Literal('binary') ^ \
                              Literal('slist')) + \
                              Suppress(Optional(idlAnnotation))
        idlBaseType.setParseAction(lambda s,l,t: [self.getType(t[0])])

        idlDefinitionType  =  idlBaseType ^ idlContainerType

        idlFieldType       << (idlBaseType ^ idlContainerType ^ \
                              idlIdentifier.copy().setParseAction(lambda s,l,t:
                                  [self.getType(t[0])])
                              )

        idlField           =  Forward()

        idlThrows          =  Junk('throws') + Junk('(') + \
                              Group(ZeroOrMore(idlField)).setResultsName('fields') + \
                              Junk(')')
        def idlThrowsAction(self,s,l,t):
            return [t]
        idlThrows.setParseAction(lambda s,l,t: idlThrowsAction(self,s,l,t))

        idlFunctionType    =  idlFieldType ^ \
                              (Literal('void').setParseAction(lambda s,l,t:
                                  [self.getType(t[0])])
                              )

        idlFunction        =  Optional(Junk('oneway')) + \
                              idlFunctionType.setResultsName('ret') + \
                              idlIdentifier.setResultsName('name') + \
                              Junk('(') + \
                              Group(ZeroOrMore(idlField)).setResultsName('params') + \
                              Junk(')') + \
                              Optional(idlThrows).setResultsName('throw') + \
                              idlListSeparator
        def idlFunctionAction(self,s,l,t):
            proc = Procedure(return_type=t['ret'], name=t['name'])
            for p in t['params']:
                proc.add_parameter(type=p['type'], optional=p['optional'], name=p['name'], default=p.get('def', False))
            if 'throw' in t:
                for f in t['throw'][0]['fields']:
                    proc.add_exception(f['type'])
            return [proc]
        idlFunction.setParseAction(lambda s,l,t: idlFunctionAction(self,s,l,t))

        idlXsdAttrs        =  Junk('xsd_attrs') + Junk('{') + \
                              Group(ZeroOrMore(idlField)).setResultsName('fields') + \
                              Junk('}')

        idlXsdFieldOptions =  Optional(Literal('xsd_optional')) + \
                              Optional(Literal('xsd_nillable')) + \
                              Optional(idlXsdAttrs)

        idlFieldReq        =  Literal('required') ^ Literal('optional')

        idlFieldID         =  idlIntConstant + Junk(':')

        idlField           << (Optional(idlFieldID) + \
                              Optional(idlFieldReq).setResultsName('req') + \
                              idlFieldType.setResultsName('type') + \
                              idlIdentifier.setResultsName('name') + \
                              Optional(Junk('=') + \
                              idlConstValue.setResultsName('def')) + \
                              idlXsdFieldOptions + \
                              Optional(idlAnnotation) + \
                              idlListSeparator)
        def idlFieldAction(self,s,l,t):
            par = {}
            par['type'] = t['type']
            par['name'] = t['name']
            par['optional'] = ('req' in t and t['req'] == 'optional')
            if 'def' in t:
                par['def'] = t['def']
            return [par]
        idlField.setParseAction(lambda s,l,t: idlFieldAction(self,s,l,t))

        idlServiceName     =  idlIdentifier.copy().setParseAction(lambda s,l,t:
                                  [self.getService(t[0])])

        idlService         =  Junk('service') + \
                              idlIdentifier.setResultsName('name') + \
                              Optional(Junk('extends') + \
                              idlServiceName.setResultsName('base')) + \
                              Junk('{') + \
                              Group(ZeroOrMore(idlFunction)).setResultsName('funcs') + \
                              Junk('}')
        def idlServiceAction(self,s,l,t):
            if not 'base' in t:
            	t['base'] = None
            con = Contract(name=t['name'], base=t['base'])
            for p in t['funcs']:
                con.add_procedure(p)
            self.setService(t['name'], con)
            return [con]
        idlService.setParseAction(lambda s,l,t: idlServiceAction(self,s,l,t))


        idlException       =  Junk('exception') + \
                              idlIdentifier.setResultsName('name') + \
                              Junk('{') + \
                              Group(ZeroOrMore(idlField)).setResultsName('fields') + \
                              Junk('}')
        def idlExceptionAction(self,s,l,t):
            str = ArsException(name=t['name'])
            for f in t['fields']:
                str.add_field(type=f['type'], optional=f['optional'], name=f['name'])
            self.setType(t['name'], str)
            return [str]
        idlException.setParseAction(lambda s,l,t: idlExceptionAction(self,s,l,t))

        idlStruct          =  Junk('struct') + \
                              idlIdentifier.setResultsName('name') + \
                              Optional(Literal('xsd_all')) + \
                              Junk('{') + \
                              Group(ZeroOrMore(idlField)).setResultsName('fields') + \
                              Junk('}') + Optional(idlAnnotation)
        def idlStructAction(self,s,l,t):
            str = Structure(name=t['name'])
            for f in t['fields']:
                str.add_field(type=f['type'], optional=f['optional'], name=f['name'])
            self.setType(t['name'], str)
            return [str]
        idlStruct.setParseAction(lambda s,l,t: idlStructAction(self,s,l,t))

        idlUnion           =  Junk('union') + \
                              idlIdentifier.setResultsName('name') + \
                              Junk('{') + \
                              Group(ZeroOrMore(idlField)).setResultsName('fields') + \
                              Junk('}')
        idlUnion.setParseAction(lambda s,l,t: idlStructureAction(self,s,l,t)) #TODO: repair it?

        idlSenum           =  Junk('senum') + \
                              idlIdentifier.setResultsName('name') + \
                              Junk('{') + \
                              Group(ZeroOrMore(
                                  idlLiteral + idlListSeparator
                              )).setResultsName('fields') + \
                              Junk('}')
        idlSenum.setParseAction(lambda s,l,t : self.setType(t['name'], Int32))

        idlEnum            =  Junk('enum') + \
                              idlIdentifier.setResultsName('name') + \
                              Junk('{') + \
                              Group(ZeroOrMore(
                                  idlIdentifier + Optional(Junk('=') + idlIntConstant) + \
                                  idlListSeparator
                              )) + \
                              Junk('}')
        idlEnum.setParseAction(lambda s,l,t : self.setType(t['name'], Int32))

        idlTypedef         =  Junk('typedef') + \
                              idlDefinitionType.setResultsName('type') + \
                              idlIdentifier.setResultsName('name')
        idlTypedef.setParseAction(lambda s,l,t :
            self.setType(t['name'], TypeAlias(target_type=t['type'], name=t['name']))
        )

        idlConst           =  Junk('const') + \
                              idlFieldType.setResultsName('type') + \
                              idlIdentifier.setResultsName('name') + \
                              Junk('=') + \
                              idlConstValue.setResultsName('value') + \
                              idlListSeparator
        idlConst.setParseAction(lambda s,l,t :
            self.setConst(t['name'], t['value'])
        )

        idlDefinition      =  idlConst ^ idlTypedef ^ idlEnum ^ idlSenum ^ \
                              idlStruct ^ idlUnion ^ idlException ^ idlService

        idlNamespaceScope  =  Literal('*') ^ Literal('cpp') ^ Literal('java') ^ \
                              Literal('py') ^ Literal('perl') ^ Literal('rb') ^ \
                              Literal('cocoa') ^ Literal('csharp') ^ Literal('js') ^ \
                              Literal('php')

        idlNamespace       =  (Junk('namespace') + \
                              ((idlNamespaceScope + idlIdentifier) ^ \
                              (Literal('smalltalk.category') + idlSTIdentifier) ^ \
                              (Literal('smalltalk.prefix') + idlIdentifier))) ^ \
                              (Literal('php_namespace') + idlIdentifier) ^ \
                              (Literal('xsd_namespace') + idlIdentifier)

        idlCppInclude      =  Junk('cpp_include') + idlLiteral

        idlInclude         =  Junk('include') +  idlLiteral

        idlHeader          =  idlInclude ^ idlCppInclude ^ idlNamespace

        idlDocument        =  Suppress(ZeroOrMore(idlHeader)) + \
                              ZeroOrMore(idlDefinition)

        idlDocument.ignore(cStyleComment)
        idlDocument.ignore(dblSlashComment)
        idlDocument.ignore(pythonStyleComment)

        self.idlDocument = idlDocument

    def readFrom(self, file):
        self.clearType()
        self.clearConst()
        self.clearService()
        thrift = file.read()
        parsed = self.idlDocument.parseString(thrift, parseAll=True)
        return self._services

