# vim:ts=4:sts=4:sw=4:expandtab
"""IDL reader for the thrift protocol.
"""

from ply import lex, yacc

from satori.objects import Argument
from satori.ars.model import *

t_ignore = ' \t\n'

literals = ':,{}()<>'

reserved = {
    'exception' : 'EXCEPTION',
    'extends': 'EXTENDS',
    'list': 'LIST',
    'map': 'MAP',
    'namespace': 'NAMESPACE',
    'optional': 'OPTIONAL',
    'required': 'REQUIRED',
    'service' : 'SERVICE',
    'struct' : 'STRUCTURE',
    'set': 'SET',
    'throws': 'THROWS',
    'typedef': 'TYPEDEF',
}

tokens = ['IDENTIFIER', 'NUMBER'] + list(reserved.values())

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z_0-9.]*'
    t.type = reserved.get(t.value, 'IDENTIFIER')    # Check for reserved words
    return t

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_error(t):
    raise RuntimeError('Illegal character \'{0}\''.format(t.value[0]))

lexer = lex.lex(debug=0)

ATOMIC_TYPES = {
    'binary': ArsBinary,
    'bool': ArsBoolean,
    'byte': ArsInt8,
    'i16': ArsInt16,
    'i32': ArsInt32,
    'i64': ArsInt64,
    'double': ArsFloat,
    'string': ArsString,
    'void': ArsVoid,
}

def p_type_list(p):
    """type : LIST '<' type '>'"""
    p[0] = ArsList(element_type=p[3])

def p_type_set(p):
    """type : SET '<' type '>'"""
    p[0] = ArsSet(element_type=p[3])

def p_type_map(p):
    """type : MAP '<' type ',' type '>'"""
    p[0] = ArsMap(key_type=p[3], value_type=p[5])

def p_type(p):
    """type : IDENTIFIER"""
    if p[1] in ATOMIC_TYPES:
        p[0] = ATOMIC_TYPES[p[1]]
    else:
        p[0] = p.parser.interface.types[p[1]]

def p_typedef(p):
    """typedef : TYPEDEF type IDENTIFIER"""
    p[0] = ArsTypeAlias(name=p[3], target_type=p[2])
    p.parser.interface.types.append(p[0])

def p_may_comma(p):
    """
    may_comma : ','
              |
    """

def p_optional_specifier_required(p):
    """optional_specifier : REQUIRED"""
    p[0] = False

def p_optional_specifier_optional(p):
    """optional_specifier : OPTIONAL"""
    p[0] = True

def p_optional_specifier_empty(p):
    """optional_specifier : """
    p[0] = False

def p_field(p):
    """field : NUMBER ':' optional_specifier type IDENTIFIER may_comma"""
    p[0] = ArsField(name=p[5], type=p[4], optional=p[3])

def p_field_list(p):
    """field_list : field_list field"""
    p[0] = p[1] + [p[2]]

def p_field_list_end(p):
    """field_list : """
    p[0] = []

def p_structure(p):
    """structure : STRUCTURE IDENTIFIER '{' field_list '}'"""
    p[0] = ArsStructure(name=p[2])
    for field in p[4]:
        p[0].add_field(field)
    p.parser.interface.types.append(p[0])

def p_exception(p):
    """exception : EXCEPTION IDENTIFIER '{' field_list '}'"""
    p[0] = ArsException(name=p[2])
    for field in p[4]:
        p[0].add_field(field)
    p.parser.interface.types.append(p[0])

def p_parameter(p):
    """parameter : NUMBER ':' optional_specifier type IDENTIFIER may_comma"""
    p[0] = ArsParameter(name=p[5], type=p[4], optional=p[3])

def p_parameter_list(p):
    """parameter_list : parameter_list parameter"""
    p[0] = p[1] + [p[2]]

def p_parameter_list_end(p):
    """parameter_list : """
    p[0] = []

def p_throws(p):
    """throws : THROWS '(' field_list ')'"""
    p[0] = [field.type for field in p[3]]

def p_throws_empty(p):
    """throws : """
    p[0] = []

def p_procedure(p):
    """procedure : type IDENTIFIER '(' parameter_list ')' throws may_comma"""
    p[0] = ArsProcedure(name=p[2], return_type=p[1])
    for parameter in p[4]:
        p[0].add_parameter(parameter)
    for exception in p[6]:
        p[0].add_exception(exception)

def p_procedure_list(p):
    """procedure_list : procedure_list procedure"""
    p[0] = p[1] + [p[2]]

def p_procedure_list_end(p):
    """procedure_list : """
    p[0] = []

def p_service_base(p):
    """service_base : EXTENDS IDENTIFIER"""
    p[0] = p.parser.interface.services[p[2]]

def p_service_base_empty(p):
    """service_base : """
    p[0] = None

def p_service(p):
    """service : SERVICE IDENTIFIER service_base '{' procedure_list '}'"""
    p[0] = ArsService(name=p[2], base=p[3])
    for procedure in p[5]:
        p[0].add_procedure(procedure)
    p.parser.interface.services.append(p[0])

def p_namespace(p):
    """namespace : NAMESPACE IDENTIFIER IDENTIFIER"""
    p[0] = None

def p_toplevel_element(p):
    """
    toplevel_element : structure
                     | exception
                     | typedef
                     | service
                     | namespace
    """

def p_toplevel_end(p):
    """toplevel : """
    p[0] = None

def p_toplevel(p):
    """toplevel : toplevel toplevel_element"""
    p[0] = None

def p_error(p):
    raise RuntimeError('Syntax error: ' + str(p))


start = 'toplevel'

parser = yacc.yacc(write_tables=0, debug=0)

class ThriftReader(object):
    def read_from(self, file):
        data = file.read()
        return self.read_from_string(data)

    def read_from_string(self, string):
        parser.interface = ArsInterface()
        parser.parse(string, lexer=lexer)
        return parser.interface

