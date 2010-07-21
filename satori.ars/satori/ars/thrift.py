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
from types import ClassType, TypeType

from pyparsing import Forward, Group, Literal, Optional, Regex, StringEnd
from pyparsing import Suppress, ZeroOrMore;
from pyparsing import cStyleComment, dblSlashComment, pythonStyleComment
from pyparsing import dblQuotedString, sglQuotedString, removeQuotes

from ..thrift.Thrift import TType, TProcessor, TMessageType, TApplicationException
from ..thrift.protocol.TProtocol import TProtocolBase
from ..thrift.server.TServer import TThreadedServer
from ..thrift.transport.TTransport import TServerTransportBase, TTransportBase
from ..thrift.protocol.TBinaryProtocol import TBinaryProtocol

from satori.objects import Object, Argument, Signature, DispatchOn, ArgumentError
from satori.ars.naming import NamedObject, NamingStyle
from satori.ars.naming import ClassName, MethodName, ParameterName, FieldName, AccessorName, Name
from satori.ars.model import Type, AtomicType, Boolean, Float, Int8, Int16, Int32, Int64, String, Void
from satori.ars.model import Field, ListType, MapType, SetType, Structure, TypeAlias
from satori.ars.model import Element, Parameter, Procedure, Contract
from satori.ars.api import Server, Reader, Client
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

    def _sendFields(self, value, name, fields, proto): # pylint: disable-msg=E0102
        proto.writeStructBegin(name)
        for index, field in enumerate(fields):
            if field is None:
                continue
            fname = self.style.format(field.name)
            fvalue = value.get(fname, None)
            if fvalue is not None:
                proto.writeFieldBegin(fname, self._ttype(field.type), index)
                self._send(fvalue, field.type, proto)
                proto.writeFieldEnd()
        proto.writeFieldStop()
        proto.writeStructEnd()

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
        self._sendFields(value, self.style.format(type_.name), [None] + [field for field in type_.fields], proto)

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
        value = self._recvFields([None] + [field for field in type_.fields], proto)
        for field in type_.fields:
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

    @DispatchOn(type_=Procedure)
    def _recv(self, type_, proto):
        fields = []
        fields.append(Field(name=Name(FieldName('success')), type=type_.return_type))
        fields.append(Field(name=Name(FieldName('error')), type=type_.error_type))
        value = self._recvFields(fields, proto)
        if 'success' in value:
            return value['success']
        raise Exception(value['error']) #TODO: what should I raise?

    @DispatchOn(type_=Procedure)
    def _send(self, value, type_, proto): # pylint: disable-msg=E0102
        fields = [None]
        for parameter in type_.parameters:
            fields.append(Field(name=parameter.name, type=parameter.type, optional=parameter.optional))
        self._sendFields(value, self.style.format(type_.name) + '_args', fields, proto)
    
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
                arguments = self._recvFields([None] + [par for par in procedure.parameters], iproto)
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
                traceback.print_exc()
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

    def call(self, name, args, iproto, oproto):
        try:
            procedure = self._procedures[name]
        except KeyError:
            raise TApplicationException(TApplicationException.UNKNOWN_METHOD,
                "Unknown method '{0}'".format(name))
        oproto.writeMessageBegin(self.style.format(procedure.name), TMessageType.CALL, self.seqid)
        self.seqid = self.seqid + 1
        self._send(args, procedure, oproto)
        oproto.writeMessageEnd()
        oproto.trans.flush()

        (fname, mtype, rseqid) = iproto.readMessageBegin()
        if mtype == TMessageType.EXCEPTION:
            x = TApplicationException()
            x.read(iproto)
            iproto.readMessageEnd()
            raise x
        result = self._recv(procedure, iproto)
        iproto.readMessageEnd()
        return result
        if result['success'] != None:
            return result['success']
        if result['error'] != None:
            raise result['error']
        raise TApplicationException(TApplicationException.MISSING_RESULT, "Static_call_me failed: unknown result");


class ThriftServer(ContractMixin, Server):
    
    @Argument('server_type', type=(ClassType, TypeType), default=TThreadedServer)
    @Argument('transport', type=TServerTransportBase)
    @Argument('changeContracts', fixed=True)
    def __init__(self, server_type, transport):
        self._server_type = server_type
        self._transport = transport
    
    def run(self):
        idl_proc = Procedure(return_type=String, name=Name(ClassName('Server'), MethodName('getIDL')))
        idl_cont = Contract(name=Name(ClassName('Server')))
        idl_cont.addProcedure(idl_proc)
        self.contracts.add(idl_cont)
        writer = ThriftWriter()
        writer.contracts.update(self.contracts)
        idl = StringIO()
        writer.writeTo(idl)
        idl = idl.getvalue()
        idl_proc.implementation = lambda: idl
        processor = ThriftProcessor(self.contracts)
        server = self._server_type(processor, self._transport)
        return server.serve()

class ThriftClient(ContractMixin, Client):

    @Argument('transport', type=TTransportBase)
    @Argument('changeContracts', fixed=True)
    def __init__(self, transport):
        self._transport = transport
        
    class Implementation(object):
        def __init__(self, client, procedure):
            self._client = client
            names = [client._processor.style.format(parameter.name) for parameter in procedure.parameters]
            self._signature = Signature(names)
            self._name = client._processor.style.format(procedure.name)
        
        def __call__(self, *args, **kwargs):
            values = self._signature.Values(*args, **kwargs)
            return self._client._processor.call(self._name, values.named, self._client._protocol, self._client._protocol)

    def start(self, bootstrap=False):
        self._transport.open()
        self._protocol = TBinaryProtocol(self._transport) #TODO: find a better protocol?
        if bootstrap:
        	self.contracts.clear()
            idl_proc = Procedure(return_type=String, name=Name(ClassName('Server'), MethodName('getIDL')))
            idl_cont = Contract(name=Name(ClassName('Server')))
            idl_cont.addProcedure(idl_proc)
            self.contracts.add(idl_cont)
            self._processor = ThriftProcessor(self.contracts)
            idl = ThriftClient.Implementation(self, idl_proc)()
            idl_reader = ThriftReader()
            idl_io = StringIO(idl)
            idl_reader.readFrom(idl_io)
            self.contracts = idl_reader.contracts
        self._processor = ThriftProcessor(self.contracts)
        for contract in self.contracts:
            for procedure in contract.procedures:
                procedure.implementation = ThriftClient.Implementation(self, procedure)
        self._changeContracts = False

    def stop(self):
        for contract in self.contracts:
            for procedure in contract.procedures:
                procedure.implementation = None
        self._transport.close()
        self._changeContracts = True


class ThriftReader(ContractMixin, ThriftBase, Reader):
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

    def setConst(self, name, type):
        self._consts[name] = type
        return [type]
    def getConst(self, name):
        return self._consts[name]
    def clearConst(self):
        self._consts = {}

    @Argument('changeContracts', fixed=False)
    def __init__(self):
        self._types = {}
        self._consts = {}
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
            str = Structure(name=Name(ClassName('exceptions')))
            for f in t['fields']:
                str.addField(type=f['type'], optional=True, name=Name(FieldName(f['name'])))
            return [str]
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
            throw = String
            if 'throw' in t and \
                isinstance(t['throw'][0], Structure) and \
                len(t['throw'][0].fields) == 1:
                for field in t['throw'][0].fields:
                    throw = field.type
            names = [n for n in self.style.parse(t['name']) if n.kind is MethodName or n.kind is AccessorName]
            name = names and names[0] or Name(MethodName(t['name']))
            proc = Procedure(return_type=t['ret'],
                       name=name,
                       error_type=throw)
            for p in t['params']:
                proc.addParameter(type=p['type'], optional=p['optional'], name=Name(ParameterName(p['name'])), default=p.get('def'))
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

        idlService         =  Junk('service') + \
                              idlIdentifier.setResultsName('name') + \
                              Optional(Junk('extends') + \
                                  idlIdentifier.setResultsName('base')) + \
                              Junk('{') + \
                              Group(ZeroOrMore(idlFunction)).setResultsName('funcs') + \
                              Junk('}')
        def idlServiceAction(self,s,l,t):
            con = Contract(name=Name(ClassName(t['name'])))
            for p in t['funcs']:
                con.addProcedure(p)
            return [con]
        idlService.setParseAction(lambda s,l,t: idlServiceAction(self,s,l,t))


        idlException       =  Junk('exception') + \
                              idlIdentifier.setResultsName('name') + \
                              Junk('{') + \
                              Group(ZeroOrMore(idlField)).setResultsName('fields') + \
                              Junk('}')
        def idlExceptionAction(self,s,l,t):
            str = Structure(name=Name(ClassName(t['name'])))
            for f in t['fields']:
                str.addField(type=f['type'], optional=f['optional'], name=Name(FieldName(f['name'])))
            self.setType(t['name'], str)
            return [str]
        idlException.setParseAction(lambda s,l,t: idlExceptionAction(self,s,l,t))

        idlStruct          =  Junk('struct') + \
                              idlIdentifier.setResultsName('name') + \
                              Optional(Literal('xsd_all')) + \
                              Junk('{') + \
                              Group(ZeroOrMore(idlField)).setResultsName('fields') + \
                              Junk('}') + Optional(idlAnnotation)
        idlStruct.setParseAction(lambda s,l,t: idlExceptionAction(self,s,l,t))

        idlUnion           =  Junk('union') + \
                              idlIdentifier.setResultsName('name') + \
                              Junk('{') + \
                              Group(ZeroOrMore(idlField)).setResultsName('fields') + \
                              Junk('}')
        idlUnion.setParseAction(lambda s,l,t: idlExceptionAction(self,s,l,t)) #TODO: repair it?

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
            self.setType(t['name'], TypeAlias(target_type=t['type'], name=Name(ClassName(t['name']))))
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
        thrift = file.read()
        self.clearType()
        self.clearConst()
        parsed = self.idlDocument.parseString(thrift, parseAll=True)
        for i in parsed:
            if isinstance(i, Contract):
                self._contracts.add(i)

#    types = property(lambda self: frozendict(self._types))
#    consts = property(lambda self: frozendict(self._consts))
    types = property(lambda self: dict(self._types))
    consts = property(lambda self: dict(self._consts))
