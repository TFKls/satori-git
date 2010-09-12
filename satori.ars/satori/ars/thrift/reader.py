# vim:ts=4:sts=4:sw=4:expandtab
"""Provider for the thrift protocol.
"""


from StringIO import StringIO
import traceback
from types import ClassType, TypeType, FunctionType
import threading
import socket

from pyparsing import Forward, Group, Literal, Optional, Regex, StringEnd
from pyparsing import Suppress, ZeroOrMore
from pyparsing import cStyleComment, dblSlashComment, pythonStyleComment
from pyparsing import dblQuotedString, sglQuotedString, removeQuotes


from satori.objects import Argument, ArgumentMode, Signature, DispatchOn
from satori.ars.model import ArsElement, ArsNamedElement, ArsNamedTuple
from satori.ars.model import ArsType, ArsNamedType, ArsTypeAlias, ArsAtomicType
from satori.ars.model import ArsList, ArsMap, ArsSet, ArsVoid, ArsBoolean
from satori.ars.model import ArsFloat, ArsInt8, ArsInt16, ArsInt32, ArsInt64, ArsString
from satori.ars.model import ArsField, ArsStructure, ArsException, ArsConstant
from satori.ars.model import ArsParameter, ArsProcedure, ArsService, ArsInterface

import sys

class ThriftReader(object):
    ATOMIC_TYPES = {
        'bool': ArsBoolean,
        'byte': ArsInt8,
        'i16': ArsInt16,
        'i32': ArsInt32,
        'i64': ArsInt64,
        'double': ArsFloat,
        'string': ArsString,
        'void': ArsVoid,
        'binary': ArsString,
        'slist': ArsString,
    }

    def add_type(self, type):
        self._interface.types.append(type)
        return [type]
    def get_type(self, name):
        if isinstance(name,ArsType):
            return name
        if name in self.ATOMIC_TYPES:
        	return self.ATOMIC_TYPES[name]
        return self._interface.types[name]

    def add_constant(self, const):
        self._interface.constants.append(const)
        return [const]
    def get_constant(self, name):
        return self._interface.constants[name]

    def add_service(self, service):
        self._interface.services.append(service)
        return [service]
    def get_service(self, name):
        return self._interface.services[name]

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
                                  [self.get_constant(t[0])]
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
            [ArsList(t['base'])]
        )

        idlSetType         =  Junk('set') + Optional(idlCppType) + Junk('<') + \
                              idlFieldType.setResultsName('base') + \
                              Junk('>')
        idlSetType.setParseAction(lambda s,l,t:
            [ArsSet(t['base'])]
        )

        idlMapType         =  Junk('map') + Optional(idlCppType) + Junk('<') + \
                              idlFieldType.setResultsName('basek') + \
                              Junk(',') + \
                              idlFieldType.setResultsName('basev') + \
                              Junk('>')
        idlMapType.setParseAction(lambda s,l,t:
            [ArsMap(t['basek'], t['basev'])]
        )

        idlContainerType   =  (idlMapType ^ idlSetType ^ idlListType) + \
                              Suppress(Optional(idlAnnotation))

        idlBaseType        =  (Literal('bool') ^ Literal('byte') ^ \
                              Literal('i16') ^ Literal('i32') ^ \
                              Literal('i64') ^ Literal('double') ^ \
                              Literal('string') ^ Literal('binary') ^ \
                              Literal('slist')) + \
                              Suppress(Optional(idlAnnotation))
        idlBaseType.setParseAction(lambda s,l,t: [self.get_type(t[0])])

        idlDefinitionType  =  idlBaseType ^ idlContainerType

        idlFieldType       << (idlBaseType ^ idlContainerType ^ \
                              idlIdentifier.copy().setParseAction(lambda s,l,t:
                                  [self.get_type(t[0])])
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
                                  [self.get_type(t[0])])
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
            proc = ArsProcedure(return_type=t['ret'], name=t['name'])
            for p in t['params']:
                proc.add_parameter(type=p['type'], optional=p['optional'], name=p['name'])
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
                                  [self.get_service(t[0])])

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
            serv = ArsService(name=t['name'], base=t['base'])
            for p in t['funcs']:
                serv.add_procedure(p)
            self.add_service(serv)
            return [serv]
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
            self.add_type(str)
            return [str]
        idlException.setParseAction(lambda s,l,t: idlExceptionAction(self,s,l,t))

        idlStruct          =  Junk('struct') + \
                              idlIdentifier.setResultsName('name') + \
                              Optional(Literal('xsd_all')) + \
                              Junk('{') + \
                              Group(ZeroOrMore(idlField)).setResultsName('fields') + \
                              Junk('}') + Optional(idlAnnotation)
        def idlStructAction(self,s,l,t):
            str = ArsStructure(name=t['name'])
            for f in t['fields']:
                str.add_field(type=f['type'], optional=f['optional'], name=f['name'])
            self.add_type(str)
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
        idlSenum.setParseAction(lambda s,l,t : self.add_type(ArsTypeAlias(name=t['name'], target_type=ArsInt32)))

        idlEnum            =  Junk('enum') + \
                              idlIdentifier.setResultsName('name') + \
                              Junk('{') + \
                              Group(ZeroOrMore(
                                  idlIdentifier + Optional(Junk('=') + idlIntConstant) + \
                                  idlListSeparator
                              )) + \
                              Junk('}')
        idlEnum.setParseAction(lambda s,l,t : self.add_type(ArsTypeAlias(name=t['name'], target_type=ArsInt32)))

        idlTypedef         =  Junk('typedef') + \
                              idlDefinitionType.setResultsName('type') + \
                              idlIdentifier.setResultsName('name')
        idlTypedef.setParseAction(lambda s,l,t :
            self.add_type(ArsTypeAlias(target_type=t['type'], name=t['name']))
        )

        idlConst           =  Junk('const') + \
                              idlFieldType.setResultsName('type') + \
                              idlIdentifier.setResultsName('name') + \
                              Junk('=') + \
                              idlConstValue.setResultsName('value') + \
                              idlListSeparator
        idlConst.setParseAction(lambda s,l,t :
            self.add_constant(ArsConstant(name=t['name'], type=t['type'], value=t['value']))
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

    def read_from(self, file):
        self._interface = ArsInterface()
        thrift = file.read()
        self.idlDocument.parseString(thrift, parseAll=True)
        return self._interface

