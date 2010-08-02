# vim:ts=4:sts=4:sw=4:expandtab

import types
from satori.objects import Signature, Argument, ReturnValue, DispatchOn
from satori.ars import model, wrapper
from satori.ars.naming import Name, ClassName, MethodName, FieldName, AccessorName
from django.db import models
from django.db.models.fields.related import add_lazy_relation
from satori.ars import perf
from satori.core.sec.tools import Token

def resolve_model(self, model, rel_model):
    self.model = model


class DjangoTypeAlias(model.TypeAlias):
    @Argument('model', type=models.base.ModelBase)
    def __init__(self, model_):
        super(DjangoTypeAlias, self).__init__(name=Name(ClassName(model_._meta.object_name + 'Id')), target_type=model.Int64)
        self.model = model_

    def needs_conversion(self):
        return True

    def convert_to_ars(self, value):
        if value is None:
        	return None

        return value.id

    def convert_from_ars(self, value):
        if value is None:
        	return None

        return self.model.objects.get(id=value)


class DjangoModelType(type):
    def __new__(mcs, name, bases, dict_):
        model = dict_['model']
        rel_model = dict_['rel_model']
        name = 'DjangoType(' + str(model) + ')'

        cls = type.__new__(mcs, name, bases, dict_)
        
        add_lazy_relation(rel_model, cls, model, resolve_model)

        return cls

    def __instancecheck__(cls, obj):
        if not isinstance(cls.model, models.base.ModelBase):
        	raise RuntimeError('{0} not resolved.'.format(cls.__name__))

        return isinstance(obj, cls.model)

    def ars_type(cls):
        if not isinstance(cls.model, models.base.ModelBase):
        	raise RuntimeError('{0} not resolved.'.format(cls.__name__))

        return cls.model.ars_type()


def DjangoModel(model, rel_model=None):
    if isinstance(model, models.base.ModelBase):
    	return model

    return DjangoModelType('', (), {'model': model, 'rel_model': rel_model})


class DjangoStructType(wrapper.StructType):
    def __new__(mcs, name, bases, dict_):
        model = dict_['model']
        name = model._meta.object_name + 'Struct'

        fields = []

        for field in model._meta.fields:
            field_type = django_field_to_python_type(model, field)
            if field_type is not None:
            	fields.append((field.name, field_type, bool(field.null)))

        fields.sort()

        dict_['fields'] = fields

        return wrapper.StructType.__new__(mcs, name, bases, dict_)


model_struct_map = {}

def DjangoStruct(model):
    if not model in model_struct_map:
        model_struct_map[model] = DjangoStructType('', (), {'model': model})

    return model_struct_map[model]


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
            field_type = DjangoModel(field.rel.to, model)
        field_type_map[field] = field_type

    return field_type_map[field]


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

    @Argument('token', type=Token)
    @Argument('self', type=model)
    @ReturnValue(type=(field_type, types.NoneType))
    def get(token, self):
        return getattr(self, field_name)

    @Argument('token', type=Token)
    @Argument('self', type=model)
    @Argument('value', type=(field_type, types.NoneType))
    @ReturnValue(type=types.NoneType)
    def set(token, self, value):
        setattr(self, field_name, value)
        self.save()
        return value

    return [set, get]


class FieldWrapper(wrapper.Wrapper):
    def __init__(self, field, parent):
        super(FieldWrapper, self).__init__(field.name, parent, FieldName)
        self._field = field

        for proc in generate_field_procedures(parent._model, field):
            self._add_child(wrapper.ProcedureWrapper(proc, self, AccessorName))


class FilterWrapper(wrapper.ProcedureWrapper):
    def __init__(self, parent):
        model = parent._model

        struct = DjangoStruct(model)
        sorted = [('token', Token, False)] + struct.fields
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
                Argument(name, type=(type, types.NoneType))(filter)

        ReturnValue(type=wrapper.TypedList(model))(filter)

        super(FilterWrapper, self).__init__(filter, parent)


class GetStructWrapper(wrapper.ProcedureWrapper):
    def __init__(self, parent):
        model = parent._model

        struct = DjangoStruct(model)

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @ReturnValue(type=struct)
        def getStruct(token, self):
            ret = {}

            for (name, type, optional) in struct.fields:
                if self.getattr(name) is not None:
                	ret[name] = self.getattr(name)

            return ret

        super(GetStructWrapper, self).__init__(getStruct, parent)


class CreateWrapper(wrapper.ProcedureWrapper):
    def __init__(self, parent):
        model = parent._model
        
        struct = DjangoStruct(model)
        sorted = [('token', Token, False)] + filter(lambda x: x[0] != 'id', struct.fields)
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
                Argument(name, type=(type, types.NoneType))(create)

#        for (name, type, optional) in sorted:
#            if optional:
#                Argument(name, type=(type, types.NoneType))(create)
#            else:
#                Argument(name, type=type)(create)

        ReturnValue(type=model)(create)
        
        super(CreateWrapper, self).__init__(create, parent)


class DeleteWrapper(wrapper.ProcedureWrapper):
    def __init__(self, parent):
        model = parent._model

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @ReturnValue(type=types.NoneType)
        def delete(token, self):
            perf.begin('delete')
            self.delete()
            perf.end('delete')

        super(DeleteWrapper, self).__init__(delete, parent)


Attribute = wrapper.Struct('Attribute', (
    ('name', str, False),
    ('isBlob', bool, False),
    ('value', str, False)
))

class OpenAttributeWrapper(wrapper.Wrapper):
    def __init__(self, parent):
        super(OpenAttributeWrapper, self).__init__('OpenAttribute', parent, ClassName)

        model = parent._model

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @ReturnValue(type=Attribute)
        def get(token, self, name):
            pass

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @ReturnValue(type=wrapper.TypedList(Attribute))
        def get_list(token, self):
            pass

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @Argument('value', type=str)
        @ReturnValue(type=types.NoneType)
        def set_str(token, self, name, value):
            pass

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('attributes', type=wrapper.TypedList(Attribute))
        @ReturnValue(type=types.NoneType)
        def set_list(token, self, attributes):
            pass

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @ReturnValue(type=types.NoneType)
        def delete(token, self, name):
            pass

        self._add_child(wrapper.ProcedureWrapper(get, self))
        self._add_child(wrapper.ProcedureWrapper(get_list, self))
        self._add_child(wrapper.ProcedureWrapper(set_str, self))
        self._add_child(wrapper.ProcedureWrapper(set_list, self))
        self._add_child(wrapper.ProcedureWrapper(delete, self))


class ModelWrapper(wrapper.StaticWrapper):
    def __init__(self, model):
        super(ModelWrapper, self).__init__(model._meta.object_name)
        self._model = model
        
        for field in model._meta.fields:
            self._add_child(FieldWrapper(field, self))

        self._add_child(FilterWrapper(self))
        self._add_child(GetStructWrapper(self))
        self._add_child(CreateWrapper(self))
        self._add_child(DeleteWrapper(self))
        self._add_child(OpenAttributeWrapper(self))

