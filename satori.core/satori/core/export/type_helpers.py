# vim:ts=4:sts=4:sw=4:expandtab

from   datetime  import datetime
from   django.db import connection, transaction
import inspect
import threading
from   types     import NoneType
import sys

from satori.ars       import perf
from satori.ars.model import *


deferred_structures = []


class ArsDeferredStructure(ArsStructure):
    def __init__(self, name, fields):
        super(ArsDeferredStructure, self).__init__(name)
        self.python_fields = fields
        deferred_structures.append(self)

    def init_fields(self):
        for (field_name, field_type, field_optional) in self.python_fields:
            self.add_field(name=field_name, type=python_to_ars_type(field_type), optional=field_optional)


class ArsDeferredException(ArsException):
    def __init__(self, name, fields):
        super(ArsDeferredException, self).__init__(name)
        self._fields = fields
        deferred_structures.append(self)

    def init_fields(self):
        for (field_name, field_type, field_optional) in self._fields:
            self.add_field(name=field_name, type=python_to_ars_type(field_type), optional=field_optional)


class TypedList(object):
    def __init__(self, element_type):
        self.element_type = element_type
    
    def ars_type(self):
        if not hasattr(self, '_ars_type'):
            self._ars_type = ArsList(python_to_ars_type(self.element_type))

        return self._ars_type


class TypedMap(object):
    def __init__(self, key_type, value_type):
        self.key_type = key_type
        self.value_type = value_type
    
    def ars_type(self):
        if not hasattr(self, '_ars_type'):
            ars_key_type = python_to_ars_type(self.key_type)
            ars_value_type = python_to_ars_type(self.value_type)
            self._ars_type = ArsMap(key_type=ars_key_type, value_type=ars_value_type)

        return self._ars_type


def Struct(name, fields):
    ars_type = ArsDeferredStructure(name, fields)
    return ars_type.get_class()


def DefineException(name, message, fields=[]):
    ars_exception = ArsDeferredException(name, [('message', str, False)] + fields)

    exception_class = ars_exception.get_class()

    def __init__(self, **kwargs):
        kwargs['message'] = unicode(message).format(**kwargs)
        super(exception_subclass, self).__init__(**kwargs)

    exception_subclass = type(name, (exception_class,), {'__init__': __init__})

    return exception_subclass

class Binary(object):
    @staticmethod
    def ars_type():
        return ArsBinary

python_basic_types = {
    NoneType: ArsVoid,
    int: ArsInt32,
    long: ArsInt64,
    str: ArsString,
    unicode: ArsString,
    basestring: ArsString,
    bool: ArsBoolean,
    datetime: ArsDateTime,
}


def python_to_ars_type(type_):
    if type_ in python_basic_types:
        return python_basic_types[type_]

    if hasattr(type_, 'ars_type'):
        return type_.ars_type()

    raise RuntimeError('Cannot convert type {0} to ars type.'.format(type_))

def init():
    for struct in deferred_structures:
        struct.init_fields()

