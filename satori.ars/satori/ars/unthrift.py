# vim:ts=4:sts=4:sw=4:expandtab
import sys
from pyparsing import Forward, Group, Literal, Optional, Regex, StringEnd
from pyparsing import Suppress, ZeroOrMore;
from pyparsing import cStyleComment, dblSlashComment, pythonStyleComment
from pyparsing import dblQuotedString, sglQuotedString, removeQuotes

from satori.objects import Object
from satori.ars.model import AtomicType, Type, Boolean, Int8, Int16
from satori.ars.model import Int32, Int64, Float, String, Void
from satori.ars.model import ListType, SetType, MapType, TypeAlias
from satori.ars.model import Procedure, Parameter, Contract, Structure
from satori.ars.naming import ClassName, MethodName, ParameterName, Name


class Junk(Suppress):
    def __init__(self, str):
        super(Junk, self).__init__(Literal(str))

class ThriftParser(Object):
    _type = {}
    def setType(self, name, type):
        self._type[name] = type
        return [type]
    def getType(self, name):
        if isinstance(name,Type):
            return name
        return self._type[name]
    def clearType(self):
        self._type = {}
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

    _const = {}
    def setConst(self, name, type):
        self._const[name] = type
        return [type]
    def getConst(self, name):
        return self._const[name]
    def clearConst(self):
        self._const = {}

    def __init__(self):
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
                str.addField(f)
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
            proc = Procedure(return_type=t['ret'],
                       name=Name(MethodName(t['name'])),
                       error_type=throw)
            for p in t['params']:
                proc.addParameter(p)
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
            par = Parameter(type=t['type'], name=Name(ParameterName(t['name'])))
            if 'req' in t and t['req'] == 'optional':
                par.optional = True
            if 'def' in t:
                par.default = t['def']
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
                str.addField(f)
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

    def parse(self, thrift):
        self.clearType()
        self.clearConst()
        parsed = self.idlDocument.parseString(thrift, parseAll=True)
        res = []
        for i in parsed:
            if isinstance(i, Contract):
            	res.append(i)
        return res
