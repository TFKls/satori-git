# vim:ts=4:sts=4:sw=4:expandtab
from datetime import datetime
from types import NoneType
from satori.objects import DispatchOn, Signature, Argument, ReturnValue, ConstraintDisjunction, ConstraintConjunction, TypeConstraint, TypedConstraint
from django.db import models
from django.db.models.fields.related import add_lazy_relation
from satori.ars import model
from satori.ars.model import NamedTuple, Contract, Procedure, Parameter
from satori.ars.naming import Name, ClassName, MethodName, FieldName, AccessorName, ParameterName, NamingStyle
import types
import typed
import typed.specialize

def resolve_model(self, model, rel_model):
    self._model = model

class DjangoModelType(typed.specialize.Type):
    def __init__(self, model, rel_model=None):
        self._model = model
        if isinstance(model, str):
            super(DjangoModelType, self).__init__(model)
            add_lazy_relation(rel_model, self, model, resolve_model)
        else:
            super(DjangoModelType, self).__init__(model._meta.object_name)

    def is_(self, x):
        if isinstance(self._model, str):
            return False
        return isinstance(x, self._model)

    def sub(self, X):
        if not isinstance(X, DjangoModelType):
            return False
        if isinstance(self._model, str) or isinstance(X._model, str):
            return False
        return issubclass(X._model, self._model)


class StructType(typed.specialize.Type):
    def __init__(self, name, fields):
        self._fields = fields
        super(StructType, self).__init__(name)

    def is_(self, x):
        for (name, type, optional) in self._fields:
            if not ((name in x) or optional):
            	return False
            if name in x:
                if not typed.isinstance(x[name], type):
                	return False
        return True

    def sub(self, X):
        if not isinstance(X, StructType):
            return False
        return self._fields == X._fields


class ModelStructType(StructType):
    def __init__(self, model):
        sorted = []

        for field in model._meta.fields:
            field_type = django_field_to_python_type(model, field)
            if field_type is not None:
            	sorted.append((field.name, field_type, bool(field.null)))

        sorted.sort()

        super(ModelStructType, self).__init__(model._meta.object_name, sorted)
        

model_type_map = {}

def django_model_to_python_type(model, rel_model=None):
    if isinstance(model, models.base.ModelBase):
        if not model in model_type_map:
        	model_type_map[model] = DjangoModelType(model, rel_model)
    	return model_type_map[model]
    else:
        return DjangoModelType(model, rel_model)

model_list_type_map = {}

def django_model_list_to_python_type(model, rel_model=None):
    if isinstance(model, models.base.ModelBase):
        if not model in model_list_type_map:
            model_list_type_map[model] = typed.List(DjangoModelType(model))
        return model_list_type_map[model]
    else:
        return typed.List(DjangoModelType(model, rel_model))

model_struct_type_map = {}

def django_model_struct_to_python_type(model):
    if isinstance(model, models.base.ModelBase):
        if not model in model_struct_type_map:
            model_struct_type_map[model] = ModelStructType(model)
        return model_struct_type_map[model]

field_basic_types = {
    models.AutoField: types.LongType,
    models.IntegerField: types.IntType,
    models.CharField: types.StringType,
    models.TextField: types.StringType,
    models.BooleanField: types.BooleanType,
}

field_type_map = {}

def django_field_to_python_type(model, field):
    if not field in field_type_map:
        field_type = None
        if type(field) in field_basic_types:
            field_type = field_basic_types[type(field)]
        if isinstance(field, models.ForeignKey):
            field_type = django_model_to_python_type(field.rel.to, model)
        field_type_map[field] = field_type

    return field_type_map[field]

python_basic_types = {
    types.NoneType: model.Void,
    types.IntType: model.Int32,
    types.LongType: model.Int64,
    types.StringType: model.String,
    types.BooleanType: model.Boolean,
}

python_type_map = {}

def python_to_ars_type(type_):
    if not type_ in python_type_map:
    	ars_type = None
    
        if type_ in python_basic_types:
        	ars_type = python_basic_types[type_]

        if isinstance(type_, models.base.ModelBase):
            ars_type = model.TypeAlias(name=Name(ClassName(type_._meta.object_name + 'Id')), target_type=model.Int64)
            ars_type.__realclass = type_

        if isinstance(type_, DjangoModelType):
            if isinstance(type_._model, str):
            	return None
            ars_type = python_to_ars_type(type_._model)

        if isinstance(type_, StructType):
        	struct = model.Structure(name=Name(ClassName(type_.name)))
            for (name, type, optional) in type_._fields:
            	struct.addField(name=Name(FieldName(name)), type=python_to_ars_type(type), optional=optional)
            ars_type = struct

        if isinstance(type_, typed.types.List_):
        	ars_element_type = python_to_ars_type(type_.T)
            if ars_element_type is None:
            	return None
            ars_type = model.ListType(ars_element_type)

        python_type_map[type_] = ars_type

    return python_type_map[type_]

def value_django_to_ars(value, ars_type):
    if isinstance(ars_type, model.ListType):
        return [value_django_to_ars(x, ars_type.element_type) for x in value]

    if hasattr(ars_type, '__realclass'):
        return value.id
               
    return value

def value_ars_to_django(value, ars_type):
    if isinstance(ars_type, model.ListType):
        return [value_ars_to_django(x, ars_type.element_type) for x in value]

    if hasattr(ars_type, '__realclass'):
        return ars_type.__realclass.objects.get(pk=value)

    return value

def emptyCan(*args, **kwargs):
    pass


def emptyFilter(*args, **kwargs):
    return args[0]


@DispatchOn(field=object)
def generate_field_procedures(model, field):
    return []

@DispatchOn(field=models.AutoField)
def generate_field_procedures(model, field):
    return []

@DispatchOn(field=models.IntegerField)
@DispatchOn(field=models.CharField)
@DispatchOn(field=models.TextField)
@DispatchOn(field=models.BooleanField)
@DispatchOn(field=models.ForeignKey)
def generate_field_procedures(model, field):
    field_name = field.name
    field_type = django_field_to_python_type(model, field)
    
    if field_type is None:
        return []

    @Argument('token', type=str)
    @Argument('self', type=model)
    @ReturnValue(type=(field_type, types.NoneType))
    def get(token, self):
        return getattr(self, field_name)

    @Argument('token', type=str)
    @Argument('self', type=model)
    @Argument('value', type=(field_type, types.NoneType))
    @ReturnValue(type=NoneType)
    def set(token, self, value):
        setattr(self, field_name, value)
        self.save()
        return value

    return [set, get]

provider_list = []
contract_list = NamedTuple()

class ProceduresProvider(object):
    def __init__(self, name, parent, name_type):
        self._children = []
        self._name = name
        self._parent = parent
        self._want = True
        self._name_type = name_type

        if parent is None:
            provider_list.append(self)

    def want(self, value):
        self._want = value

    def _add_child(self, child):
        self._children.append(child)
        setattr(self, child._name, child)

    def _generate_procedures(self):
        ret = NamedTuple()
        if not self._want:
            return ret

        for child in self._children:
            ret.extend(child._generate_procedures())

        ret.update_prefix(self._name_type(self._name))

        return ret


class ProcedureProvider(ProceduresProvider):
    def __init__(self, implement, parent, name_type=MethodName):
        super(ProcedureProvider, self).__init__(implement.__name__, parent, name_type)

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
        ret = NamedTuple()
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
    
        ars_proc = Procedure(name=Name(self._name_type(self._name)), return_type=model.Void, implementation = proc)
        ret.add(ars_proc)

        return ret


class FieldProceduresProvider(ProceduresProvider):
    def __init__(self, field, parent):
        super(FieldProceduresProvider, self).__init__(field.name, parent, FieldName)
        self._field = field

        for proc in generate_field_procedures(parent._model, field):
            self._add_child(ProcedureProvider(proc, self, AccessorName))


class FilterProcedureProvider(ProcedureProvider):
    def __init__(self, parent):
        model = parent._model

        struct = django_model_struct_to_python_type(model)
        sorted = [('token', str, False)] + struct._fields
        names = [x[0] for x in sorted]

        def filter(token, *args, **kwargs):
            for i in range(len(args)):
                if args[i] is not None:
                    kwargs[names[i + 1]] = args[i]

            return model.objects.filter(**kwargs)

        sign = Signature(names)
        sign.set(filter)

        for (name, type, optional) in sorted:
            if name == 'token':
                Argument(name, type=type)(filter)
            else:
                Argument(name, type=(type, NoneType))(filter)

        ReturnValue(type=django_model_list_to_python_type(model))(filter)

        super(FilterProcedureProvider, self).__init__(filter, parent)


class GetStructProcedureProvider(ProcedureProvider):
    def __init__(self, parent):
        model = parent._model

        struct = django_model_struct_to_python_type(model)

        @Argument('token', type=str)
        @Argument('self', type=model)
        @ReturnValue(type=struct)
        def getStruct(token, self):
            ret = {}

            for (name, type, optional) in struct._fields:
                if self.getattr(name) is not None:
                	ret[name] = self.getattr(name)

            return ret

        super(GetStructProcedureProvider, self).__init__(getStruct, parent)

class CreateProcedureProvider(ProcedureProvider):
    def __init__(self, parent):
        model = parent._model
        
        struct = django_model_struct_to_python_type(model)
        sorted = [('token', str, False)] + filter(lambda x: x[0] != 'id', struct._fields)
        names = [x[0] for x in sorted]

        def create(token, *args, **kwargs):
            for i in range(len(args)):
                if args[i] is not None:
                    kwargs[names[i + 1]] = args[i]

            ret = model(**kwargs)
            ret.save()
            return ret

        sign = Signature(names)
        sign.set(create)

        for (name, type, optional) in sorted:
            if name == 'token':
                Argument(name, type=type)(create)
            else:
                Argument(name, type=(type, NoneType))(create)

#        for (name, type, optional) in sorted:
#            if optional:
#                Argument(name, type=(type, NoneType))(create)
#            else:
#                Argument(name, type=type)(create)

        ReturnValue(type=model)(create)
        
        super(CreateProcedureProvider, self).__init__(create, parent)

class DeleteProcedureProvider(ProcedureProvider):
    def __init__(self, parent):
        model = parent._model

        @Argument('token', type=str)
        @Argument('self', type=model)
        @ReturnValue(type=NoneType)
        def delete(token, self):
            self.delete()

        super(DeleteProcedureProvider, self).__init__(delete, parent)

class StaticProceduresProvider(ProceduresProvider):
    def __init__(self, name):
        super(StaticProceduresProvider, self).__init__(name, None, ClassName)

    def method(self, proc):
        self._add_child(ProcedureProvider(proc, self, MethodName))


class ModelProceduresProvider(StaticProceduresProvider):
    def __init__(self, model):
        super(ModelProceduresProvider, self).__init__(model._meta.object_name)
        self._model = model
        
        for field in model._meta.fields:
            self._add_child(FieldProceduresProvider(field, self))

        self._add_child(FilterProcedureProvider(self))
        self._add_child(GetStructProcedureProvider(self))
        self._add_child(CreateProcedureProvider(self))
        self._add_child(DeleteProcedureProvider(self))


class OpersBase(type):
    def __new__(cls, name, bases, dict_):
        newdict = {}

        for elem in dict_.itervalues():
            if isinstance(elem, ProceduresProvider):
                for (proc_name, ars_proc) in elem._generate_procedures().PYTHON.iteritems():
                    newdict[proc_name] = staticmethod(ars_proc.implementation)
                    
        return super(OpersBase, cls).__new__(cls, name, bases, newdict)

    def __init__(cls, name, bases, dict_):
        super(OpersBase, cls).__init__(name, bases, dict_)

class Opers(object):
    __metaclass__ = OpersBase

def is_nonetype_constraint(constraint):
    return isinstance(constraint, TypeConstraint) and (constraint.type == NoneType)

def extract_ars_type(constraint):
    if isinstance(constraint, ConstraintDisjunction):
        if len(constraint.members) == 2:
            if is_nonetype_constraint(constraint.members[0]):
                return (extract_ars_type(constraint.members[1])[0], True)
            elif is_nonetype_constraint(constraint.members[1]):
                return (extract_ars_type(constraint.members[0])[0], True)

    if isinstance(constraint, TypeConstraint):
        return (python_to_ars_type(constraint.type), False)

    if isinstance(constraint, TypedConstraint):
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
        ars_proc.addParameter(Parameter(name=Name(ParameterName(signature.positional[i])), type=param_type[0], optional=param_type[1]))
        ars_arg_types.append(param_type[0])

    want_token = (arg_count > 0) and (signature.positional[0] == 'token')
    
    def reimplementation(**kwargs):
        newargs = [None] * arg_count
#        if want_token:
#           args[0] = process_token(args[0])

        for i in range(arg_count):
            if arg_names[i] in kwargs:
                # should not be none
                newargs[i] = value_ars_to_django(kwargs[arg_names[i]], ars_arg_types[i])
            else:
                newargs[i] = None

        ret = implementation(*newargs)

        ret = value_django_to_ars(ret, ars_ret_type)
 
#        if ret is None:
#           raise NoneReturn()

        return ret

    ars_proc.implementation = reimplementation

def generate_contract(provider):
    contract = Contract(name=Name(ClassName(provider._name)))

    for ars_proc in provider._generate_procedures().items:
        wrap(ars_proc)
        contract.addProcedure(ars_proc)

    return contract

def generate_contracts():
    if not contract_list.items:
        for provider in provider_list:
            contract_list.add(generate_contract(provider))

