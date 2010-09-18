# vim:ts=4:sts=4:sw=4:expandtab

from types import NoneType
from datetime import datetime
from satori.objects import Signature, Argument, ReturnValue, DispatchOn
from satori.ars.wrapper import StructType, Struct, TypedList, Wrapper, ProcedureWrapper, StaticWrapper
from satori.ars.model import ArsInt64, ArsTypeAlias
from django.db import models, transaction
from django.db.models.fields.related import add_lazy_relation
from satori.core.sec.tools import Token
from satori.core.models import OpenAttribute, Blob

def resolve_model(self, model, rel_model):
    self.model = model


class ArsDjangoModel(ArsTypeAlias):
    @Argument('model', type=models.base.ModelBase)
    def __init__(self, model):
        super(ArsDjangoModel, self).__init__(name=(model._meta.object_name + 'Id'), target_type=ArsInt64)
        self.model = model
        
    def do_needs_conversion(self):
        return True

    def do_convert_to_ars(self, value):
        return value.id

    def do_convert_from_ars(self, value):
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


class DjangoStructType(StructType):
    def __new__(mcs, name, bases, dict_):
        model = dict_['model']
        name = model._meta.object_name + 'Struct'

        fields = []

        for field in model._meta.fields:
            field_type = django_field_to_python_type(model, field)
            if (field.name != 'model') and (not field.name.startswith('parent_')) and (field_type is not None):
                fields.append((field.name, field_type, True))

        fields.sort()

        dict_['fields'] = fields

        return StructType.__new__(mcs, name, bases, dict_)


model_struct_map = {}

def DjangoStruct(model):
    if not model in model_struct_map:
        model_struct_map[model] = DjangoStructType('', (), {'model': model})

    return model_struct_map[model]


field_basic_types = {
    models.AutoField: long,
    models.IntegerField: int,
    models.CharField: str,
    models.TextField: str,
    models.BooleanField: bool,
    models.DateTimeField: datetime,
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
@DispatchOn(field=models.DateTimeField)
@DispatchOn(field=models.ForeignKey)
def generate_field_procedures(model, field):
    field_name = field.name
    field_type = django_field_to_python_type(model, field)
    
    if field_type is None:
        return []

    @Argument('token', type=Token)
    @Argument('self', type=model)
    @ReturnValue(type=(field_type, NoneType))
    def get(token, self):
        return getattr(self, field_name)

    @Argument('token', type=Token)
    @Argument('self', type=model)
    @Argument('value', type=field_type)
    @ReturnValue(type=NoneType)
    def set(token, self, value=None):
        setattr(self, field_name, value)
        self.save()
        return value

    return [set, get]


class FieldWrapper(Wrapper):
    def __init__(self, field, parent):
        super(FieldWrapper, self).__init__(field.name, parent)
        self._field = field

        for proc in generate_field_procedures(parent._model, field):
            self._add_child(ProcedureWrapper(proc, self))


class FilterWrapper(ProcedureWrapper):
    def __init__(self, parent):
        model = parent._model

        @Argument('token', type=Token)
        @Argument('values', type=DjangoStruct(model))
        @ReturnValue(type=TypedList(model))
        def filter(token, values={}):
            return model.objects.filter(**values)

        super(FilterWrapper, self).__init__(filter, parent)


class GetStructWrapper(ProcedureWrapper):
    def __init__(self, parent):
        model = parent._model

        struct = DjangoStruct(model)

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @ReturnValue(type=struct)
        def get_struct(token, self):
            ret = {}

            for (name, type, optional) in struct.fields:
                ret[name] = getattr(self, name)

            return ret

        super(GetStructWrapper, self).__init__(get_struct, parent)


class SetStructWrapper(ProcedureWrapper):
    def __init__(self, parent):
        model = parent._model

        struct = DjangoStruct(model)

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('value', type=struct)
        @ReturnValue(type=NoneType)
        def set_struct(token, self, value):
            for (name, type, optional) in struct.fields:
                if (name in value) and (name != 'id'):
                    setattr(self, name, value[name])
            self.save()

        super(SetStructWrapper, self).__init__(set_struct, parent)


class CreateWrapper(ProcedureWrapper):
    def __init__(self, parent):
        model = parent._model
        
        @Argument('token', type=Token)
        @Argument('values', type=DjangoStruct(model))
        @ReturnValue(type=model)
        def create(token, values):
            if 'id' in values:
                del values['id']

            ret = model(**values)
            ret.save()
            return ret
        
        super(CreateWrapper, self).__init__(create, parent)


class DeleteWrapper(ProcedureWrapper):
    def __init__(self, parent):
        model = parent._model

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @ReturnValue(type=NoneType)
        def delete(token, self):
            self.delete()

        super(DeleteWrapper, self).__init__(delete, parent)


class DemandRightWrapper(ProcedureWrapper):
    def __init__(self, parent):
        model = parent._model

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('right', type=str)
        @ReturnValue(type=bool)
        def demand_right(token, self, right):
            return self.demand_right(token, right)

        super(DemandRightWrapper, self).__init__(demand_right, parent)


Attribute = Struct('Attribute', (
    ('name', str, False),
    ('is_blob', bool, False),
    ('value', str, False)
))

class OpenAttributeWrapper(Wrapper):
    def __init__(self, parent):
        super(OpenAttributeWrapper, self).__init__('oa', parent)

        model = parent._model

        def oa_to_struct(oa):
            ret = {}
            ret['name'] = oa.name
            if oa.oatype == OpenAttribute.OATYPES_BLOB:
                ret['is_blob'] = True
                ret['value'] = oa.blob.hash
            elif oa.oatype == OpenAttribute.OATYPES_STRING:
                ret['is_blob'] = False
                ret['value'] = oa.string_value
            return ret

        def struct_to_oa(self, struct):
            try:
                oa = self.attributes.get(name=struct['name'])
            except:
                oa = OpenAttribute(object=self, name=struct['name'])
            if struct['is_blob']:
                oa.oatype = OpenAttribute.OATYPES_BLOB
                oa.blob = Blob.objects.get(hash=struct['value'])
            else:
                oa.oatype = OpenAttribute.OATYPES_STRING
                oa.string_value = struct['value']
            oa.save()

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @ReturnValue(type=(Attribute, NoneType))
        def get(token, self, name):
            try:
                oa = self.attributes.get(name=name)
            except:
                return None
            return oa_to_struct(self.attributes.get(name=name))

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @ReturnValue(type=str)
        def get_str(token, self, name):
            try:
                oa = self.attributes.get(name=name)
            except:
                return None
            struct = oa_to_struct(oa)
            if struct['is_blob']:
            	raise Exception('The attribute is not a string attribute')
            return struct['value']

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @ReturnValue(type=str)
        def get_blob(token, self, name):
            raise Exception('Not implemented')

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @ReturnValue(type=str)
        def get_blob_hash(token, self, name):
            try:
                oa = self.attributes.get(name=name)
            except:
                return None
            struct = oa_to_struct(oa)
            if not struct['is_blob']:
            	raise Exception('The attribute is not a blob attribute')
            return struct['value']

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @ReturnValue(type=TypedList(Attribute))
        def get_list(token, self):
            return [oa_to_struct(oa) for oa in self.attributes.all()]

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('value', type=Attribute)
        @ReturnValue(type=NoneType)
        def set(token, self, value):
            struct_to_oa(self, value)

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @Argument('value', type=str)
        @ReturnValue(type=NoneType)
        def set_str(token, self, name, value):
            struct_to_oa(self, {'name': name, 'value': value, 'is_blob': False})
        
        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @Argument('value', type=str)
        @ReturnValue(type=NoneType)
        def set_blob(token, self, name, value):
            raise Exception('Not implemented.')


        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @Argument('value', type=str)
        @ReturnValue(type=NoneType)
        def set_blob_hash(token, self, name, value):
            struct_to_oa(self, {'name': name, 'value': value, 'is_blob': True})

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('attributes', type=TypedList(Attribute))
        @ReturnValue(type=NoneType)
        def set_list(token, self, attributes):
            for struct in attributes:
            	struct_to_oa(self, struct)

        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @ReturnValue(type=NoneType)
        def delete(token, self, name):
            self.attributes.get(name=name).delete()

        self._add_child(ProcedureWrapper(get, self))
        self._add_child(ProcedureWrapper(get_str, self))
        self._add_child(ProcedureWrapper(get_blob, self))
        self._add_child(ProcedureWrapper(get_blob_hash, self))
        self._add_child(ProcedureWrapper(get_list, self))
        self._add_child(ProcedureWrapper(set, self))
        self._add_child(ProcedureWrapper(set_str, self))
        self._add_child(ProcedureWrapper(set_blob, self))
        self._add_child(ProcedureWrapper(set_blob_hash, self))
        self._add_child(ProcedureWrapper(set_list, self))
        self._add_child(ProcedureWrapper(delete, self))


class ModelWrapperClass(StaticWrapper):
    def __init__(self, model):
        if len(model._meta.parents) > 1:
            raise Exception('Wrappers don\'t support models with multiple bases.')

        base_wrapper = None
        if model._meta.parents:
            base_wrapper = ModelWrapper(model._meta.parents.keys()[0])

        super(ModelWrapperClass, self).__init__(model._meta.object_name, base_wrapper)
        self._model = model
        
#        for field in model._meta.local_fields:
#            self._add_child(FieldWrapper(field, self))

        self._add_child(FilterWrapper(self))
        self._add_child(GetStructWrapper(self))
        self._add_child(SetStructWrapper(self))
        self._add_child(CreateWrapper(self))
        self._add_child(DeleteWrapper(self))


model_wrappers = {}

def ModelWrapper(model):
    if model not in model_wrappers:
        model_wrappers[model] = ModelWrapperClass(model)
    return model_wrappers[model]


class TransactionMiddleware(object):
    """
    Transaction middleware. If this is enabled, each function will be run
    in its own transaction - that way a save() doesn't do a direct
    commit, the commit is done when a successful response is created. If an
    exception happens, the database is rolled back.
    """
    def process_request(self, args, kwargs):
        """Enters transaction management"""
        print 'tenter'
        transaction.enter_transaction_management()
        transaction.managed(True)

    def process_exception(self, args, kwargs, exception):
        """Rolls back the database and leaves transaction management"""
        print 'texcept'
        if transaction.is_dirty():
            transaction.rollback()
        transaction.leave_transaction_management()

    def process_response(self, args, kwargs, ret):
        """Commits and leaves transaction management."""
        print 'tleave'
        if transaction.is_managed():
            if transaction.is_dirty():
                transaction.commit()
            transaction.leave_transaction_management()
        return ret

