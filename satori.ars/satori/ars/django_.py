# vim:ts=4:sts=4:sw=4:expandtab
from types import NoneType
from satori.objects import DispatchOn, Signature, Argument, ReturnValue, ConstraintDisjunction, ConstraintConjunction, TypeConstraint
from django.db import models
from django.db.models.fields.related import add_lazy_relation
from satori.ars.model import NamedTuple, Contract, Procedure, Parameter, TypeAlias, Void, Boolean, Int32, Int64, String, ListType
from satori.ars.naming import Name, ClassName, MethodName, FieldName, AccessorName, ParameterName, NamingStyle

class TypedList(type):
    def __init__(self, name, bases, namespace):
        super(TypedList, self).__init__(name, bases, {})
        self.type_ = namespace['type']


class LazyModelClass(type):
    def __init__(self, model_name):
        self.model_name = model_name

def emptyCan(*args, **kwargs):
    pass


def emptyFilter(*args, **kwargs):
    return args[0]


def process_constraint(constraint, model):
    return
    if instanceof(constraint, (ConstraintConjunction, ConstraintDisjunction)):
        for member in constraint.members:
            process_constraint(member, model)

    if instanceof(constraint, TypeConstraint):
        if instanceof(constraint.type, LazyModelClass) and (constraint.type.model_name == model._meta.object_name):
            constraint.type = model
        if instanceof(constraint.type, TypedList) and (constraint.type.type == model._meta.object_name):
        	constraint.type.type = model


def fix_arg_ret_model(func, model, cls):
    sign = Signature.of(func)
    for argument in sign.arguments.itervalues():
        process_constraint(argument.constraint, model)

    process_constraint(sign.return_value.constraint)


@DispatchOn(field=object)
def generate_field_procedures(model, field):
    return []

@DispatchOn(field=models.AutoField)
def generate_field_procedures(model, field):
    return []

@DispatchOn(field=models.ForeignKey)
def generate_field_procedures(model, field):
    field_name = field.name
    other = field.rel.to
    if isinstance(other, str):
    	other = LazyModelClass(other)
    ret = []

    @Argument('token', type=str)
    @Argument('self', type=model)
    @ReturnValue(type=(other, NoneType))
    def get(token, self):
        return getattr(self, field_name)

    @Argument('token', type=str)
    @Argument('self', type=model)
    @Argument('value', type=(other, NoneType))
    @ReturnValue(type=NoneType)
    def set(token, self, value):
        setattr(self, field_name, value)
        self.save()
        return value

    if isinstance(other, basestring):
        add_lazy_relation(model, get, other, fix_arg_ret_model)
        add_lazy_relation(model, set, other, fix_arg_ret_model)

    return [set, get]

@DispatchOn(field=models.IntegerField)
@DispatchOn(field=models.CharField)
def generate_field_procedures(model, field):
    type_mapping = {
            models.IntegerField: int,
            models.CharField: str
            }

    field_name = field.name
    ret = []

    @Argument('token', type=str)
    @Argument('self', type=model)
    @ReturnValue(type=type_mapping[type(field)])
    def get(token, self):
        return getattr(self, field_name)

    @Argument('token', type=str)
    @Argument('self', type=model)
    @Argument('value', type=type_mapping[type(field)])
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
    
        ars_proc = Procedure(name=Name(self._name_type(self._name)), return_type=Void, implementation = proc)
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
        names = []
        types = []

        for field in model._meta.fields:
        	field_ok = True

            if isinstance(field, models.IntegerField):
            	types.append(int)
            elif isinstance(field, models.CharField):
                types.append(str)
            elif isinstance(field, models.ForeignKey):
                other = field.rel.to
                if isinstance(other, str):
                    types.append(LazyModelClass(other))
                else:
                	types.append(other)
            else:
            	field_ok = False
            
            if field_ok:
            	names.append(field.name)

        sorted = zip(names, types)
        sorted.sort()
        sorted = [('token', str)] + sorted
        (names, types) = zip(*sorted)

        def filter(token, *args, **kwargs):
            for i in range(len(args)):
                if args[i] is not None:
                	kwargs[names[i + 1]] = args[i]
            ret = model.objects.filter(**kwargs)
            return ret

        sign = Signature(names)
        sign.set(filter)

        for (name, type_) in zip(names, types):
        	Argument(name, type=(type_, NoneType))(filter)

        ReturnValue(type=TypedList('A', (object,), {'type': model}))(filter)

        super(FilterProcedureProvider, self).__init__(filter, parent)


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

id_types = {}
rev_id_types = {}

def get_id_type(model):
    if not isinstance(model, models.base.ModelBase):
        raise RuntimeError("Argument is not an instance of ModelBase: " + model)
    if not model in id_types:
        id_types[model] = TypeAlias(name=Name(ClassName(model._meta.object_name + 'Id')), target_type=Int64)
        rev_id_types[id_types[model]] = model
    return id_types[model]

def is_nonetype_constraint(constraint):
    if isinstance(constraint, TypeConstraint) and (constraint.type == NoneType):
        return True
    else:
        return False

def extract_type(constraint):
    if isinstance(constraint, ConstraintDisjunction):
        if len(constraint.members) == 2:
            if is_nonetype_constraint(constraint.members[0]):
                return (extract_type(constraint.members[1])[0], True)
            else:
                if is_nonetype_constraint(constraint.members[1]):
                    return (extract_type(constraint.members[0])[0], True)

    if isinstance(constraint, TypeConstraint):
    	return (constraint.type, False)

    raise RuntimeError("Cannot extract type from constraint: " + str(constraint))

types = {
        NoneType: Void,
        str: String,
        int: Int32,
}

def ars_type(type_):
    if isinstance(type_, models.base.ModelBase):
        return get_id_type(type_)

    if isinstance(type_, TypedList):
    	return ListType(ars_type(type_.type_))
    
    if type_ in types:
        return types[type_]

    raise RuntimeError("Cannot convert type to ars type: " + str(type_))

def convert_to(elem, type):
    if isinstance(type, ListType):
        return [convert_to(x, type.element_type) for x in elem]

    if type in rev_id_types:
        return elem.id
               
    return elem

def convert_from(elem, type):
    if isinstance(type, ListType):
        return [convert_from(x, type.element_type) for x in elem]

    if type in rev_id_types:
        return rev_id_types[type].objects.get(pk=elem)

    return elem

def wrap(ars_proc):
    implementation = ars_proc.implementation
    signature = Signature.of(implementation)

    ars_ret_type = ars_type(extract_type(signature.return_value.constraint)[0])
    ars_proc.return_type = ars_ret_type

    arg_names = signature.positional
    arg_count = len(signature.positional)
    ars_arg_types = []
    for i in range(arg_count):
        param_type = extract_type(signature.arguments[signature.positional[i]].constraint)
        ars_proc.addParameter(Parameter(name=Name(ParameterName(signature.positional[i])), type=ars_type(param_type[0]), optional=param_type[1]))
        ars_arg_types.append(ars_type(param_type[0]))

    want_token = (arg_count > 0) and (signature.positional[0] == 'token')
    
    def reimplementation(**kwargs):
        newargs = [None] * arg_count
#        if want_token:
#           args[0] = process_token(args[0])

        for i in range(arg_count):
            if arg_names[i] in kwargs:
                # should not be none
                newargs[i] = convert_from(kwargs[arg_names[i]], ars_arg_types[i])
            else:
            	newargs[i] = None

        ret = implementation(*newargs)

        ret = convert_to(ret, ars_ret_type)
 
#        if ret is None:
#        	raise NoneReturn()

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

