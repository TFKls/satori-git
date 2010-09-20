# vim:ts=4:sts=4:sw=4:expandtab

from collections import Sequence, Mapping
from datetime import datetime
from time import mktime
from types import NoneType, FunctionType
import sys
import copy
from satori.objects import Signature, Argument, ArgumentMode, ReturnValue, ConstraintDisjunction, TypeConstraint
from satori.ars.model import ArsInterface, ArsTypeAlias, ArsList, ArsMap, ArsStructure, ArsProcedure, ArsService
from satori.ars.model import ArsVoid, ArsInt32, ArsInt64, ArsString, ArsBoolean

class ArsNullableStructure(ArsStructure):
    def __init__(self, name):
        super(ArsNullableStructure, self).__init__(name)
        self.add_field(name='null_fields', type=ArsInt64, optional=True)

    def do_needs_conversion(self):
        return True

    def do_convert_to_ars(self, value):
        value['null_fields'] = 0L

        for (ind, field) in enumerate(self.fields):
            if (field.name in value) and (value[field.name] is None):
            	value['null_fields'] = value['null_fields'] | (1 << (ind + self.base_index))
            	del value[field.name]

        return super(ArsNullableStructure, self).do_convert_to_ars(value)

    def do_convert_from_ars(self, value):
        value = super(ArsNullableStructure, self).do_convert_from_ars(value)

        if not 'null_fields' in value:
        	return value

        for (ind, field) in enumerate(self.fields):
            if value['null_fields'] & (1 << (ind + self.base_index)):
                value[field.name] = None
        
        del value['null_fields']

        return value


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


class StructType(type):
    def __new__(mcs, name, bases, dict_):
        assert 'fields' in dict_
        dict_['name'] = name
        return type.__new__(mcs, name, bases, dict_)

    def __instancecheck__(cls, obj):
        for (name, type_, optional) in cls.fields:
            if not ((name in obj) or optional):
                return False
            if name in obj:
                if not isinstance(obj[name], type_):
                    return False
        return True

    def ars_type(cls):
        if not hasattr(cls, '_ars_type'):
            cls._ars_type = ArsNullableStructure(name=cls.name)
            for (field_name, field_type, field_optional) in cls.fields:
                cls._ars_type.add_field(name=field_name, type=python_to_ars_type(field_type), optional=field_optional)

        return cls._ars_type


def Struct(name, fields):
    return StructType(name, (), {'fields': fields})


class ArsDateTime(ArsTypeAlias):
    def __init__(self, ):
        super(ArsDateTime, self).__init__(name='DateTime', target_type=ArsInt64)

    def do_needs_conversion(self):
        return True

    def do_convert_to_ars(self, value):
        return long(mktime(value.timetuple()))

    def do_convert_from_ars(self, value):
        return datetime.fromtimestamp(value)


python_basic_types = {
    NoneType: ArsVoid,
    int: ArsInt32,
    long: ArsInt64,
    str: ArsString,
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
    signature = Signature.of(proc)

    ars_ret_type = extract_ars_type(signature.return_value.constraint)

    arg_names = signature.positional
    arg_count = len(signature.positional)
    ars_arg_types = []
    ars_arg_optional = []
    arg_numbers = {}
    for i in range(arg_count):
        argument = signature.arguments[signature.positional[i]]
        param_type = extract_ars_type(argument.constraint)
        optional = argument.mode == ArgumentMode.OPTIONAL
        ars_arg_types.append(param_type)
        ars_arg_optional.append(optional)
        arg_numbers[signature.positional[i]] = i

    def reimplementation(*args, **kwargs):
        args = list(args)
    
        for i in middleware:
            i.process_request(args, kwargs)
        
        try:
            newargs = []
            newkwargs = {}
            for i in range(min(len(args), arg_count)):
                newargs.append(ars_arg_types[i].convert_from_ars(args[i]))

            for arg_name in kwargs:
                newkwargs[arg_name] = ars_arg_types[arg_numbers[arg_name]].convert_from_ars(kwargs[arg_name])

            ret = proc(*newargs, **newkwargs)

            ret = ars_ret_type.convert_to_ars(ret)
        except Exception as exception:
            for i in reversed(middleware):
                i.process_exception(args, kwargs, exception)
            raise
        else:
            for i in reversed(middleware):
                ret = i.process_response(args, kwargs, ret)
            return ret

    ars_proc = ArsProcedure(name=name, implementation=reimplementation, return_type=ars_ret_type)

    for i in range(arg_count):
        ars_proc.add_parameter(name=signature.positional[i], type=ars_arg_types[i], optional=ars_arg_optional[i])

    return ars_proc

def generate_service(wrapper, base):
    service = ArsService(name=wrapper._name, base=base)

    for (name, proc) in wrapper._generate_procedures().iteritems():
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

    return interface


def register_middleware(obj):
    middleware.append(obj)

