# vim:ts=4:sts=4:sw=4:expandtab

#import abc
import collections
import types
from satori.objects import Signature, Argument, ReturnValue, ConstraintDisjunction, TypeConstraint
from satori.ars import model
from satori.ars.naming import Name, ClassName, MethodName, FieldName, ParameterName

class ArsWrapperType(type):
    __subclass__ = set()
    __instance__ = set()

    def ars_type(cls):
        raise NotImplemented()
    
    @classmethod
    def isinstance(cls, inst):
        sub = type(inst)
        return (any(issubclass(inst, c) for c in cls.__instance__) 
            or any(issubclass(sub, c) for c in cls.__subclass__))

    @classmethod
    def register_subclass(cls, sub):
        cls.__subclass__.add(sub)

    @classmethod
    def register_instance(cls, inst):
        cls.__instance__.add(inst)

ArsWrapperType.register_subclass(ArsWrapperType)


class TypedListType(ArsWrapperType):
    def __new__(mcs, name, bases, dict_):
        elem_type = dict_['elem_type']
        name = 'list[' + str(elem_type) + ']'
        return ArsWrapperType.__new__(mcs, name, bases, dict_)

    def __instancecheck__(cls, obj):
        if not isinstance(elem, collections.Sequence):
        	return False

        for elem in obj:
            if not isinstance(elem, cls.elem_type):
            	return False

        return True

    def ars_type(cls):
        if not hasattr(cls, '_ars_type'):
        	cls._ars_type = model.ListType(python_to_ars_type(cls.elem_type))

        return cls._ars_type


def TypedList(elem_type):
    return TypedListType('', (), {'elem_type': elem_type})


class TypedMapType(ArsWrapperType):
    def __new__(mcs, name, bases, dict_):
        key_type = dict_['key_type']
        value_type = dict_['value_type']
        name = 'map[' + str(key_type) + ',' + str(value_type) + ']'
        return ArsWrapperType.__new__(mcs, name, bases, dict_)

    def __instancecheck__(cls, obj):
        if not isinstance(elem, collections.Mapping):
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
        	cls._ars_type = model.MapType(key_type=ars_key_type, value_type=ars_value_type)

        return cls._ars_type


def TypedMap(key_type, value_type):
    return TypedMapType('', (), {'key_type': key_type, 'value_type': value_type})


class StructType(ArsWrapperType):
    def __new__(mcs, name, bases, dict_):
        assert 'fields' in dict_
        dict_['name'] = name
        return ArsWrapperType.__new__(mcs, name, bases, dict_)

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
        	cls._ars_type = model.Structure(name=Name(ClassName(cls.name)))
            for (name, type_, optional) in cls.fields:
            	cls._ars_type.addField(name=Name(FieldName(name)), type=python_to_ars_type(type_), optional=optional)

        return cls._ars_type


def Struct(name, fields):
    return StructType(name, (), {'fields': fields})


python_basic_types = {
    types.NoneType: model.Void,
    types.IntType: model.Int32,
    types.LongType: model.Int64,
    types.StringType: model.String,
    types.BooleanType: model.Boolean,
}

def python_to_ars_type(type_):
    if type_ in python_basic_types:
    	return python_basic_types[type_]

    if ArsWrapperType.isinstance(type_):
    	return type_.ars_type()

    raise RuntimeError('Cannot convert type {0} to ars type.'.format(type_))


wrapper_list = []
contract_list = model.NamedTuple()


class Wrapper(object):
    def __init__(self, name, parent, name_type):
        self._children = []
        self._name = name
        self._parent = parent
        self._want = True
        self._name_type = name_type

        if parent is None:
            wrapper_list.append(self)

    def want(self, value):
        self._want = value

    def _add_child(self, child):
        self._children.append(child)
        setattr(self, child._name, child)

    def _generate_procedures(self):
        ret = model.NamedTuple()
        if not self._want:
            return ret

        for child in self._children:
            ret.extend(child._generate_procedures())

        ret.update_prefix(self._name_type(self._name))

        return ret


def emptyCan(*args, **kwargs):
    pass


def emptyFilter(retval, *args, **kwargs):
    return retval


class ProcedureWrapper(Wrapper):
    def __init__(self, implement, parent, name_type=MethodName):
        super(ProcedureWrapper, self).__init__(implement.__name__, parent, name_type)

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
        ret = model.NamedTuple()
        if not self._want:
            return ret

        can = self._can
        filter = self._filter
        implement = self._implement

        def proc(*args, **kwargs):
            can(*args, **kwargs)
            result = implement(*args, **kwargs)
            return filter(result, *args, **kwargs)

        Signature.of(implement).set(proc)
    
        ars_proc = model.Procedure(name=Name(self._name_type(self._name)), return_type=model.Void, implementation = proc)
        ret.add(ars_proc)

        return ret

class StaticWrapper(Wrapper):
    def __init__(self, name):
        super(StaticWrapper, self).__init__(name, None, ClassName)

    def method(self, proc):
        self._add_child(ProcedureWrapper(proc, self, MethodName))


class WrapperBase(type):
    def __init__(cls, name, bases, dict_):
        newdict = {}

        for elem in dict_.itervalues():
            if isinstance(elem, Wrapper):
                for (proc_name, ars_proc) in elem._generate_procedures().PYTHON.iteritems():
                    newdict[proc_name] = staticmethod(ars_proc.implementation)
                    
        return super(WrapperBase, cls).__init__(name, bases, newdict)

class WrapperClass(object):
    __metaclass__ = WrapperBase

def is_nonetype_constraint(constraint):
    return isinstance(constraint, TypeConstraint) and (constraint.type == types.NoneType)

def extract_ars_type(constraint):
    if isinstance(constraint, ConstraintDisjunction):
        if len(constraint.members) == 2:
            if is_nonetype_constraint(constraint.members[0]):
                return (extract_ars_type(constraint.members[1])[0], True)
            elif is_nonetype_constraint(constraint.members[1]):
                return (extract_ars_type(constraint.members[0])[0], True)

    if isinstance(constraint, TypeConstraint):
        return (python_to_ars_type(constraint.type), False)

    raise RuntimeError("Cannot extract type from constraint: " + str(constraint))


def wrap(ars_proc):
    implementation = ars_proc.implementation
    signature = Signature.of(implementation)

    ars_ret_type = extract_ars_type(signature.return_value.constraint)[0]
    ars_proc.return_type = ars_ret_type

    arg_names = signature.positional
    arg_count = len(signature.positional)
    ars_arg_types = []
    for i in range(arg_count):
        param_type = extract_ars_type(signature.arguments[signature.positional[i]].constraint)
        ars_proc.addParameter(model.Parameter(name=Name(ParameterName(signature.positional[i])), type=param_type[0], optional=param_type[1]))
        ars_arg_types.append(param_type[0])

    def reimplementation(*args, **kwargs):
        newargs = [None] * arg_count

        for i in range(arg_count):
            if i < len(args):
            	newargs[i] = ars_arg_types[i].convert_from_ars(args[i])
            if arg_names[i] in kwargs:
                newargs[i] = ars_arg_types[i].convert_from_ars(kwargs[arg_names[i]])
            else:
                newargs[i] = None

        ret = implementation(*newargs)

        return ars_ret_type.convert_to_ars(ret)

    ars_proc.implementation = reimplementation

def generate_contract(wrapper):
    contract = model.Contract(name=Name(ClassName(wrapper._name)))

    for ars_proc in wrapper._generate_procedures().items:
        wrap(ars_proc)
        contract.addProcedure(ars_proc)

    return contract

def generate_contracts():
    if not contract_list.items:
        for wrapper in wrapper_list:
            contract_list.add(generate_contract(wrapper))

    return contract_list

