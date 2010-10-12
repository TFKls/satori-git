# vim:ts=4:sts=4:sw=4:expandtab

from collections import Sequence, Mapping
from datetime import datetime
from operator import itemgetter
from time import mktime
from types import NoneType, FunctionType
import sys
import copy
from satori.objects import Signature, Argument, ArgumentMode, ReturnValue, ConstraintDisjunction, TypeConstraint
from satori.ars.model import *
from satori.ars import perf

class ArsNullableStructure(ArsStructure):
    def __init__(self, name):
        super(ArsNullableStructure, self).__init__(name)
        self.add_field(name='null_fields', type=ArsInt64, optional=True)

    def do_needs_conversion(self):
        return True

    def do_convert_to_ars(self, value):
        if isinstance(value, dict):
            value = self.get_class()(value)

        value.null_fields = 0L

        for (ind, field) in enumerate(self.fields):
            if hasattr(value, field.name):
                if getattr(value, field.name) is None:
                    value.null_fields = value.null_fields | (1L << (ind + self.base_index))
            else:
                setattr(value, field.name, None)

        return super(ArsNullableStructure, self).do_convert_to_ars(value)

    def do_convert_from_ars(self, value):
        value = super(ArsNullableStructure, self).do_convert_from_ars(value)

        null_fields = getattr(value, 'null_fields', 0L)

        for (ind, field) in enumerate(self.fields):
            if null_fields & (1L << (ind + self.base_index)):
                setattr(value, field.name, None)
            elif hasattr(value, field.name) and (getattr(value, field.name) is None):
                delattr(value, field.name)

        if hasattr(value, 'null_fields'):
            delattr(value, 'null_fields')

        return value

    def get_class(self):
        if not hasattr(self, '_class'):
            def __init__(self, dict_=None, **kwargs):
                super(_class, self).__init__()
                if dict_:
                    kwargs.update(dict_)
                for field_name in self._field_names:
                    if field_name in kwargs:
                        setattr(self, field_name, kwargs.pop(field_name))
                if kwargs:
                    raise TypeError('__init__() got an unexpected keyword argument \'{0}\''.format(kwargs.keys()[0]))

            @classmethod
            def ars_type(cls):
                return cls._ars_type

            field_names = [field.name for field in self.fields][1:]

            _class = type(self.name, (object,), {'__init__': __init__, 'ars_type': ars_type, '_ars_type': self, '_field_names': field_names,
                            '__setitem__': lambda x, y, z: setattr(x, y, z),
                            '__getitem__': lambda x, y: getattr(x, y),
                            '__delitem__': lambda x, y: delattr(x, y),
                            '__contains__': lambda x, y: hasattr(x, y)
                    })
            self._class = _class
        return self._class


class TypedListType(type):
    def __new__(mcs, name, bases, dict_):
        elem_type = dict_['elem_type']
        name = 'list[' + str(elem_type) + ']'
        return type.__new__(mcs, name, bases, dict_)

    def __instancecheck__(cls, obj):
        if not isinstance(elem, Sequence):
            return False

        for elem in obj:
            if not isinstance(elem, cls.elem_type):
                return False

        return True

    def ars_type(cls):
        if not hasattr(cls, '_ars_type'):
            cls._ars_type = ArsList(python_to_ars_type(cls.elem_type))

        return cls._ars_type


def TypedList(elem_type):
    return TypedListType('', (), {'elem_type': elem_type})


class TypedMapType(type):
    def __new__(mcs, name, bases, dict_):
        key_type = dict_['key_type']
        value_type = dict_['value_type']
        name = 'map[' + str(key_type) + ',' + str(value_type) + ']'
        return type.__new__(mcs, name, bases, dict_)

    def __instancecheck__(cls, obj):
        if not isinstance(elem, Mapping):
            return False

        for (key, value) in obj.items:
            if not isinstance(key, cls.key_type):
                return False
            if not isinstance(value, cls.value_type):
                return False

        return True

    def ars_type(cls):
        if not hasattr(cls, '_ars_type'):
            ars_key_type = python_to_ars_type(cls.key_type)
            ars_value_type = python_to_ars_type(cls.value_type)
            cls._ars_type = ArsMap(key_type=ars_key_type, value_type=ars_value_type)

        return cls._ars_type


def TypedMap(key_type, value_type):
    return TypedMapType('', (), {'key_type': key_type, 'value_type': value_type})


#class StructType(type):
#    def __new__(mcs, name, bases, dict_):
#        assert 'fields' in dict_
#        dict_['name'] = name
#        return type.__new__(mcs, name, bases, dict_)
#
#    def __instancecheck__(cls, obj):
#        for (name, type_, optional) in cls.fields:
#            if not ((name in obj) or optional):
#                return False
#            if name in obj:
#                if not isinstance(obj[name], type_):
#                    return False
#        return True
#
#    def ars_type(cls):
#        if not hasattr(cls, '_ars_type'):
#            cls._ars_type = ArsNullableStructure(name=cls.name)
#            for (field_name, field_type, field_optional) in cls.fields:
#                cls._ars_type.add_field(name=field_name, type=python_to_ars_type(field_type), optional=field_optional)
#
#        return cls._ars_type


def Struct(name, fields):
    ars_type = ArsNullableStructure(name=name)
    for (field_name, field_type, field_optional) in fields:
        ars_type.add_field(name=field_name, type=python_to_ars_type(field_type), optional=field_optional)
    return ars_type.get_class()


class ArsDateTime(ArsTypeAlias):
    def __init__(self, ):
        super(ArsDateTime, self).__init__(name='DateTime', target_type=ArsInt64)

    def do_needs_conversion(self):
        return True

    def do_convert_to_ars(self, value):
        return long(mktime(value.timetuple()))

    def do_convert_from_ars(self, value):
        return datetime.fromtimestamp(value)


def DefineException(name, message, fields=[]):
    ars_exception = ArsException(name=name)
    ars_exception.add_field(name='message', type=ArsString, optional=False)
    for (field_name, field_type, field_optional) in fields:
        ars_exception.add_field(name=field_name, type=python_to_ars_type(field_type), optional=field_optional)

    exception_class = ars_exception.get_class()

    def __init__(self, **kwargs):
        kwargs['message'] = message.format(**kwargs)
        super(exception_subclass, self).__init__(**kwargs)

    exception_subclass = type(name, (exception_class,), {'__init__': __init__})

    return exception_subclass


python_basic_types = {
    NoneType: ArsVoid,
    int: ArsInt32,
    long: ArsInt64,
    str: ArsString,
    unicode: ArsString,
    basestring: ArsString,
    bool: ArsBoolean,
    datetime: ArsDateTime(),
}

def python_to_ars_type(type_):
    if type_ in python_basic_types:
        return python_basic_types[type_]

    if hasattr(type_, 'ars_type'):
        return type_.ars_type()

    raise RuntimeError('Cannot convert type {0} to ars type.'.format(type_))


wrapper_list = []
constants = {}
global_throwss = []
middleware = []

class Wrapper(object):
    @Argument('name', type=str)
    def __init__(self, name, parent, base=None):
        if parent and base:
            raise Exception('Wrapper cannot have base and parent')

        self._children = []
        self._name = name
        self._parent = parent
        self._want = True
        self._base = base

        if parent is None:
            wrapper_list.append(self)

    def want(self, value):
        self._want = value

    def _add_child(self, child):
        self._children.append(child)
        setattr(self, child._name, child)

    def _generate_procedures(self):
        procs = {}
        ret = {}
        if not self._want:
            return ret

        for child in self._children:
            procs.update(child._generate_procedures())

        for (name, proc) in procs.iteritems():
            ret[self._name + '_' + name] = proc

        return ret

    def _fill_module(self, name):
        module = sys.modules[name]

        procs = self._generate_procedures()

        for (name, proc) in procs.iteritems():
            setattr(module, name, proc)

        setattr(module, '__all__', procs.keys())


def emptyCan(*args, **kwargs):
    return True


def emptyFilter(retval, *args, **kwargs):
    return retval


class ProcedureWrapper(Wrapper):
    @Argument('implement', type=FunctionType)
    def __init__(self, implement, parent):
        super(ProcedureWrapper, self).__init__(implement.__name__, parent)

        self._can = emptyCan
        self._filter = emptyFilter
        self._implement = implement

    def can(self, proc):
        self._can = proc
        return proc

    def filter(self, proc):
        self._filter = proc
        return proc

    def implement(self, proc):
        self._implement = proc
        return proc

    def _generate_procedures(self):
        ret = {}
        if not self._want:
            return ret

        can = self._can
        filter = self._filter
        implement = self._implement

        def proc(*args, **kwargs):
            if not can(*args, **kwargs):
                raise Exception('Access denied.')
            result = implement(*args, **kwargs)
            return filter(result, *args, **kwargs)

        Signature.of(implement).set(proc)
        proc.implementation = implement

        ret[self._name] = proc

        def proc(*args, **kwargs):
            return can(*args, **kwargs)

        copy.copy(Signature.of(implement)).set(proc)
        Signature.of(proc).return_value = ReturnValue(type=bool)

        ret[self._name + '_can'] = proc

        return ret


class StaticWrapper(Wrapper):
    def __init__(self, name, base=None):
        super(StaticWrapper, self).__init__(name, None, base)

    def method(self, proc):
        self._add_child(ProcedureWrapper(proc, self))


class TypeConversionMiddleware(object):
    def process_request(self, proc, args, kwargs):
        for i in range(min(len(args), len(proc.parameters))):
            args[i] = proc.parameters[i].type.convert_from_ars(args[i])

        for arg_name in kwargs:
            kwargs[arg_name] = proc.parameters[arg_name].type.convert_from_ars(kwargs[arg_name])

    def process_exception(self, proc, args, kwargs, exception):
        if isinstance(exception, ArsExceptionBase):
            return exception.ars_type().convert_to_ars(exception)
        else:
            return exception

    def process_response(self, proc, args, kwargs, ret):
        return proc.return_type.convert_to_ars(ret)


def is_nonetype_constraint(constraint):
    return isinstance(constraint, TypeConstraint) and (constraint.type == NoneType)

def extract_ars_type(constraint):
    if isinstance(constraint, ConstraintDisjunction):
        if len(constraint.members) == 2:
            if is_nonetype_constraint(constraint.members[0]):
                return extract_ars_type(constraint.members[1])
            elif is_nonetype_constraint(constraint.members[1]):
                return extract_ars_type(constraint.members[0])

    if isinstance(constraint, TypeConstraint):
        return python_to_ars_type(constraint.type)

    raise RuntimeError("Cannot extract type from constraint: " + str(constraint))


def generate_procedure(name, proc):
    ars_proc = None

    def reimplementation(*args, **kwargs):
        args = list(args)

        try:
            perf.begin('mid req')
            for i in middleware:
                i.process_request(ars_proc, args, kwargs)
            perf.end('mid req')

            perf.begin('proc')
            ret = proc(*args, **kwargs)
            perf.end('proc')

            perf.begin('mid resp')
            for i in reversed(middleware):
                ret = i.process_response(ars_proc, args, kwargs, ret)
            perf.end('mid resp')
        except Exception as exception:
            for i in reversed(middleware):
                exception = i.process_exception(ars_proc, args, kwargs, exception)
            raise exception, None, sys.exc_info()[2]
        else:
            return ret

    signature = Signature.of(proc)
    ret_type = extract_ars_type(signature.return_value.constraint)

    ars_proc = ArsProcedure(name=name, implementation=reimplementation, return_type=ret_type)

    for arg_name in signature.positional:
        argument = signature.arguments[arg_name]
        arg_type = extract_ars_type(argument.constraint)
        arg_optional = (argument.mode == ArgumentMode.OPTIONAL)

        ars_proc.add_parameter(name=arg_name, type=arg_type, optional=arg_optional)

    for exception in global_throwss:
        ars_proc.add_exception(python_to_ars_type(exception))

    for exception in signature.exceptions:
        ars_proc.add_exception(python_to_ars_type(exception))

    return ars_proc

def constant(name, value):
    constants[name] = value

def global_throws(exception):
    global_throwss.append(exception)

def generate_service(wrapper, base):
    service = ArsService(name=wrapper._name, base=base)

    for (name, proc) in sorted(wrapper._generate_procedures().items(), key=itemgetter(0)):
        service.add_procedure(generate_procedure(name, proc))

    return service


def generate_interface():
    interface = ArsInterface()

    for wrapper in wrapper_list:
        if wrapper._base:
            base = interface.services[wrapper._base._name]
        else:
            base = None
        interface.add_service(generate_service(wrapper, base))

    for (name, value) in constants.items():
        ars_type = python_to_ars_type(type(value))
        interface.add_constant(name=name, value=ars_type.convert_to_ars(value), type=ars_type)

    return interface


def register_middleware(obj):
    middleware.append(obj)

