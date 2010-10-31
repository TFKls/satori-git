# vim:ts=4:sts=4:sw=4:expandtab

import os
from   sphinx.application import Sphinx
import sphinx.ext.autodoc
import shutil
import sys

from satori.ars.model import *

from sphinx.addnodes import desc_parameter, desc_returns
from sphinx.domains.python import PythonDomain, PyClassmember
from docutils.statemachine import ViewList
from sphinx.util.docfields import DocFieldTransformer

class PyRichMethod(PyClassmember):
    def handle_signature(self, sig, signode):
        ret = super(PyRichMethod, self).handle_signature(sig, signode)
        for child in signode.traverse(desc_parameter):
            t = child[0]
            del child[0]
            l = ViewList()
            l.append(t.astext(), '<AA>')
            self.state.nested_parse(l, 0, child)
            DocFieldTransformer(self).transform_all(child)
        for child in signode.traverse(desc_returns):
            t = child[0]
            del child[0]
            l = ViewList()
            l.append(t.astext(), '<AA>')
            self.state.nested_parse(l, 0, child)
            DocFieldTransformer(self).transform_all(child)
        return ret

PythonDomain.directives['richmethod'] = PyRichMethod


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

def reference_type(type):
    if isinstance(type, ArsAtomicType):
        return {
            ArsBoolean: ':py:class:`bool`',
            ArsInt8:    ':py:class:`byte`',
            ArsInt16:   ':py:class:`i16`',
            ArsInt32:   ':py:class:`i32`',
            ArsInt64:   ':py:class:`i64`',
            ArsFloat:   ':py:class:`double`',
            ArsString:  ':py:class:`string`',
            ArsVoid:    ':py:class:`void`',
        }[type]
    elif isinstance(type, ArsList):
        return 'list<{0}>'.format(reference_type(type.element_type))
    elif isinstance(type, ArsMap):
        return 'map<{0}, {1}>'.format(reference_type(type.key_type), reference_type(type.value_type))
    elif isinstance(type, ArsNamedType):
        return ':py:class:`{0}`'.format(type.name)
    else:
        raise RuntimeError('Cannot reference type: {0}'.format(str(type)))


def generate_type(f, type_name):
    type = ars_interface.types[type_name]

    f.write(T("""
        .
        {0}
        {1}
        .. py:class:: {0}
        
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
                .. py:attribute:: {0}

                  Type: {2}
            
            {1}
            """).format(field.name, prepare_doc(field, 6), reference_type(field.type)))


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
        Below are functions defined by attribute group ``oa`` for the :py:class:`Entity` class.
        Other attribute groups define similar functions, with ``oa`` changed to the group name
        and they may require different permissions instead of ATTRIBUTE_READ and ATTRIBUTE_WRITE.
        """))

    for procedure in ars_interface.services['Entity'].procedures:
        if procedure.name.startswith('Entity_oa_'):
            procedure_name = procedure.name.split('_', 1)[1]
            signature = ','.join('{1} {0}'.format(param.name, reference_type(param.type)) for param in list(procedure.parameters)[2:])

            f.write(T("""
                .
                  .. py:richmethod:: {0}({2}) -> {3}

                {1}
                """).format(procedure_name, prepare_doc(procedure, 4), signature, reference_type(procedure.return_type)))

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
        .. py:class:: {0}
        
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
                                Inherited from :py:class:`{0}`:
                            """).format(base.name))
                        add = 2
                    else:
                        add = 0

                    for (method_name, method) in sorted(methods[method_type][base].items()):
                        signature = ','.join('{1} {0}'.format(param.name, reference_type(param.type)) for param in list(method.parameters)[method_type + 1:])

                        if base == service:
                            inherited = ''
                        else:
                            inherited = 'Inherited from :py:class:`{0}`'.format(base.name)

                        f.write(T("""
                            .
                                {2}.. py:richmethod:: {0}({3}) -> {4}

                            {1}
                            """).format(method_name, prepare_doc(method, 6 + add), ' ' * add, signature, reference_type(method.return_type)))

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

