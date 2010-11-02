# vim:ts=4:sts=4:sw=4:expandtab

import os
from   sphinx.application import Sphinx
import sphinx.ext.autodoc
import shutil
import sys

from satori.ars.model import *

from docutils import nodes
from sphinx import addnodes
from sphinx.domains import Domain, ObjType, BUILTIN_DOMAINS 
from sphinx.directives import ObjectDescription
from sphinx.roles import XRefRole
from sphinx.util.nodes import make_refnode


atomic_type_names = {
    ArsBoolean: 'bool',
    ArsInt8:    'byte',
    ArsInt16:   'i16',
    ArsInt32:   'i32',
    ArsInt64:   'i64',
    ArsFloat:   'double',
    ArsString:  'string',
    ArsVoid:    'void',
}


def gen_type_node(node, type):
    if isinstance(type, ArsAtomicType):
        node += nodes.literal(atomic_type_names[type], atomic_type_names[type])
    elif isinstance(type, ArsList):
        node += nodes.literal('list', 'list')
        node += nodes.Text('<')
        gen_type_node(node, type.element_type)
        node += nodes.Text('>')
    elif isinstance(type, ArsMap):
        node += nodes.literal('map', 'map')
        node += nodes.Text('<')
        gen_type_node(node, type.key_type)
        node += nodes.Text(',')
        gen_type_node(node, type.value_type)
        node += nodes.Text('>')
    elif isinstance(type, ArsNamedType):
        refnode = addnodes.pending_xref('', refdomain='ars', reftype='type', reftarget=type.name, modname=None, classname=None)
        refnode += nodes.literal(type.name, type.name)
        node += refnode
    else:
        raise RuntimeError('Cannot reference type: {0}'.format(str(type)))


class ArsTypeDirective(ObjectDescription):
    def before_content(self):
        self.env.temp_data['ars:typename'] = self.type.name
    
    def after_content(self):
        del self.env.temp_data['ars:typename']

    def handle_signature(self, sig, signode):
        self.type = ars_interface.types[sig.strip()]

        if isinstance(self.type, ArsException):
            signode += nodes.literal('exception', 'exception')
            signode += nodes.Text(' ')
            signode += addnodes.desc_name(self.type.name, self.type.name)
        elif isinstance(self.type, ArsStructure):
            signode += nodes.literal('structure', 'structure')
            signode += nodes.Text(' ')
            signode += addnodes.desc_name(self.type.name, self.type.name)
        elif isinstance(self.type, ArsTypeAlias):
            signode += nodes.literal('typedef', 'typedef')
            signode += nodes.Text(' ')
            signode += addnodes.desc_name(self.type.name, self.type.name)
            signode += nodes.Text(' ')
            gen_type_node(signode, self.type.target_type)
        else:
            raise RuntimeError('Cannot generate type definition: {0}'.format(str(self.type)))

        return self.type.name


class ArsFieldDirective(ObjectDescription):
    def handle_signature(self, sig, signode):
        sig = sig.strip()

        parent = self.env.temp_data.get('ars:typename', None)

        if not parent:
            in_parent = False

            split = sig.split('.', 1)

            if len(split) == 2:
                parent = split[0]
                name = split[1]
            else:
                raise RuntimeError('Parent not found')
        else:
            in_parent = True
            name = sig

        self.type = ars_interface.types[parent]
        self.field = self.type.fields[name]
        
        gen_type_node(signode, self.field.type)
        signode += nodes.Text(' ')
        if not in_parent:
            signode += addnodes.addname(self.type.name, self.type.name)
            signode += nodes.Text('.')
        signode += addnodes.desc_name(self.field.name, self.field.name)
        
        return self.type.name + '.' + self.field.name


class ArsServiceDirective(ObjectDescription):
    def before_content(self):
        self.env.temp_data['ars:servicename'] = self.service.name
    
    def after_content(self):
        del self.env.temp_data['ars:servicename']

    def handle_signature(self, sig, signode):
        self.service = ars_interface.services[sig.strip()]

        signode += nodes.literal('service', 'service')
        signode += nodes.Text(' ')
        signode += addnodes.desc_name(self.service.name, self.service.name)

        return self.service.name


class ArsProcedureDirective(ObjectDescription):
    option_spec = {
        'skipargs': int,
    }
    
    def handle_signature(self, sig, signode):
        sig = sig.strip()

        parent = self.env.temp_data.get('ars:servicename', None)

        if not parent:
            in_parent = False

            split = sig.split('.', 1)

            if len(split) == 2:
                parent = split[0]
                name = split[1]
            else:
                raise RuntimeError('Parent not found')
        else:
            in_parent = True
            name = sig

        self.service = ars_interface.services[parent]

        base = self.service
        self.procedure = None
        while base is not None:
            if base.name + '_' + name in base.procedures:
                self.procedure = base.procedures[base.name + '_' + name]
                break
            base = base.base

        if not self.procedure:
            raise RuntimeError('Procedure {0} not found in {1} or base services'.format(name, parent))

        skipargs = self.options.get('skipargs', 0)
        
        gen_type_node(signode, self.procedure.return_type)
        signode += nodes.Text(' ')

        if not in_parent:
            signode += addnodes.desc_addname(self.service.name, self.service.name)
            signode += nodes.Text('.')
        signode += addnodes.desc_name(name, name)

        paramlist_node = addnodes.desc_parameterlist()
        for param in list(self.procedure.parameters)[skipargs:]:
            param_node = addnodes.desc_parameter('', '', noemph=True)
            gen_type_node(param_node, param.type)
            param_node += nodes.Text(' ')
            param_node += nodes.emphasis(param.name, param.name)
            paramlist_node += param_node
        signode += paramlist_node

        if self.procedure.exception_types:
            signode += nodes.Text(' ')
            signode += nodes.literal('throws', 'throws')
            signode += nodes.Text(' (')
            first = True
            for exception in self.procedure.exception_types:
                if first:
                    first = False
                else:
                    signode += nodes.Text(', ')
                gen_type_node(signode, exception)
            signode += nodes.Text(')')

        return self.service.name + '.' + self.procedure.name


class ArsDomain(Domain):
    name = 'ars'
    label = 'ARS'
    object_types = {
        'type': ObjType('type', 'type'),
        'field': ObjType('field', 'field'),
        'service': ObjType('service', 'service'),
        'procedure': ObjType('procedure', 'procedure'),
    }
    directives = {
        'type': ArsTypeDirective,
        'field': ArsFieldDirective,
        'service': ArsServiceDirective,
        'procedure': ArsProcedureDirective,
    }
    roles = {
        'type': XRefRole(),
        'field': XRefRole(),
        'service': XRefRole(),
        'procedure': XRefRole(),
    }


BUILTIN_DOMAINS['ars'] = ArsDomain


def prepare_doc(obj, indent):
    doc = obj.__dict__.get('__doc__', None)

    if doc is None:
        return ''

    return '\n'.join(' ' * indent + docline for docline in doc.split('\n'))


def T(text):
    lines = text.split('\n')

    if lines:
        del lines[0]

    if not lines:
        return ''

    counter = 0
    while (len(lines[0]) > counter) and (lines[0][counter] == ' '):
        counter += 1

    return '\n'.join(line[counter:] for line in lines[1:]) + '\n'


def generate_type(f, type_name):
    type = ars_interface.types[type_name]

    f.write(T("""
        .
        {0}
        {1}
        .. ars:type:: {0}
        
        {2}
        """).format(type_name, '-' * len(type_name), prepare_doc(type, 2)))

    if not isinstance(type, ArsStructure):
        return

    f.write(T("""
        .
          Instance attributes:
        """))

    for field in type.fields:
        f.write(T("""
            .
                .. ars:field:: {0}
            
            {1}
            """).format(field.name, prepare_doc(field, 6)))


def generate_index(f, service_names):
    f.write(T("""
        .
        Satori API documentation
        ========================
        
        .. toctree::
          :hidden:
        
          types
          exceptions
          oa
        """))

    for service_name in service_names:
        f.write(T("""
            .
              service_{0}
            """).format(service_name))

    f.close()


def generate_exceptions(f, exception_names):
    f.write(T("""
        .
        Exception types
        ===============
        """))

    for exception_name in exception_names:
        generate_type(f, exception_name)

    f.close()


def generate_types(f, type_names):
    f.write(T("""
        .
        Simple types
        ============
        """))

    for type_name in type_names:
        generate_type(f, type_name)

    f.close()


def generate_oa(f):
    f.write(T("""
        .
        Open attributes
        ===============
        Every class can have defined several open attribute groups that are identified by name. 
        Every open attribute group behaves like a list of (name, value) pairs, where name is a string
        and value can be a string or a blob. If value is a blob, it can hold filename together with the data.

        There are two ways to access open attributes: Thrift functions and blob server (using HTTP).

        Thrift API
        ----------
        Every attribute group defines a set of instance methods for class instances.
        Below are functions defined by attribute group ``oa`` for the :cpp:class:`Entity` class.
        Other attribute groups define similar functions, with ``oa`` changed to the group name
        and they may require different permissions instead of ATTRIBUTE_READ and ATTRIBUTE_WRITE.
        """))

    for procedure in ars_interface.services['Entity'].procedures:
        if procedure.name.startswith('Entity_oa_'):
            procedure_name = procedure.name.split('_', 1)[1]

            f.write(T("""
                .
                  .. ars:procedure:: Entity.{0}
                    :skipargs: 2

                {1}
                """).format(procedure_name, prepare_doc(procedure, 4)))

    f.write(T("""
        .
        Blob server
        -----------
        TBD
        """))

    f.close()


def generate_service(f, service_name):
    f.write(T("""
        .
        {0}
        {1}
        """).format(service_name, '=' * len(service_name)))

    if service_name + 'Id' in ars_interface.types:
        generate_type(f, service_name + 'Id')

    if service_name + 'Struct' in ars_interface.types:
        generate_type(f, service_name + 'Struct')

    service = ars_interface.services[service_name]

    methods = ({}, {})

    methods_so_far = (set(), set())

    base = service
    while base is not None:
        for method in base.procedures:
            method_name = method.name.split('_', 1)[1]

            if (len(method.parameters) >= 2) and (method.parameters[1].name == 'self'):
                method_type = 1
            else:
                method_type = 0

            if method_name not in methods_so_far[method_type]:
                methods[method_type].setdefault(base, {})[method_name] = method
                methods_so_far[method_type].add(method_name)

        base = base.base

    f.write(T("""
        .
        {0}
        {1}
        .. ars:service:: {0}
        
        {2}
        """).format(service_name, '-' * len(service_name), prepare_doc(service, 2)))

    for method_type in (0, 1):
        if methods[method_type]:
            f.write(T("""
                .
                  {0} methods:

                """).format('Static' if method_type == 0 else 'Instance'))

            base = service
            while base is not None:
                if base in methods[method_type]:
                    if base != service:
                        f.write(T("""
                            .
                                Inherited from :ars:service:`{0}`:
                            """).format(base.name))
                        add = 2
                    else:
                        add = 0

                    for (method_name, method) in sorted(methods[method_type][base].items()):

                        if base == service:
                            inherited = ''
                        else:
                            inherited = 'Inherited from :ars:service:`{0}`'.format(base.name)

                        f.write(T("""
                            .
                                {2}.. ars:procedure:: {0}
                                {2}  :skipargs: {3}

                            {1}
                            """).format(method_name, prepare_doc(method, 6 + add), ' ' * add, 1 + method_type))

                base = base.base

    f.close()


def generate_api_doc():
    os.environ['DJANGO_SETTINGS_MODULE'] = 'satori.core.settings'
    
    global ars_interface
    from satori.core.api import ars_interface

    if len(sys.argv) != 2:
        print >>sys.stderr, 'Usage: {0} <target directory>'.format(sys.argv[0])
        exit(1)

    destdir = sys.argv[1]
    srcdir = os.path.join(destdir, '_input')

    if os.path.exists(destdir):
        shutil.rmtree(destdir)

    os.makedirs(os.path.join(srcdir))

    service_names = sorted(ars_interface.services.names)
    type_names = []
    exception_names = []

    for type_name in sorted(ars_interface.types.names):
        if type_name.endswith('Id') and (type_name[:-2] in service_names):
            continue
        if type_name.endswith('Struct') and (type_name[:-6] in service_names):
            continue
        if isinstance(ars_interface.types[type_name], ArsException):
            exception_names.append(type_name)
        else:
            type_names.append(type_name)

    generate_index(open(os.path.join(srcdir, 'index.rst'), 'w'), service_names)
    generate_types(open(os.path.join(srcdir, 'types.rst'), 'w'), type_names)
    generate_exceptions(open(os.path.join(srcdir, 'exceptions.rst'), 'w'), exception_names)
    generate_oa(open(os.path.join(srcdir, 'oa.rst'), 'w'))

    for service_name in service_names:
        generate_service(open(os.path.join(srcdir, 'service_{0}.rst'.format(service_name)), 'w'), service_name)
    
    conf = {
        'project': 'Satori API',
        'version': '1',
        'release': '1',
        'master_doc': 'index',
        'html_sidebars': {
            '**': ['globaltoc.html', 'searchbox.html'],
        },
    }

    app = Sphinx(srcdir, None, destdir, os.path.join(destdir, '.doctrees'), 'html',
                 conf, sys.stdout, sys.stderr, True, False, [])

    app.build(True, [])

    return app.statuscode

