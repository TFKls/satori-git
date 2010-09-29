# vim:ts=4:sts=4:sw=4:expandtab

from types import NoneType
from datetime import datetime
from satori.objects import Signature, Argument, ReturnValue, DispatchOn
from satori.ars.wrapper import StructType, Struct, TypedList, TypedMap, Wrapper, ProcedureWrapper, StaticWrapper
from satori.ars.model import *
from django.db import models, transaction, connection
from django.db.models.fields.related import add_lazy_relation
from satori.core.sec.tools import Token
from satori.core.models import OpenAttribute, Blob, Privilege

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
    models.IPAddressField: str,
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


def can_view(token, object):
    return object.demand_right(token, 'VIEW')


def can_edit(token, object):
    return object.demand_right(token, 'EDIT')


class FieldWrapper(Wrapper):
    def __init__(self, field, parent):
        super(FieldWrapper, self).__init__(field.name, parent)
        self._field = field
        self._can_read = can_view
        self._can_write = can_edit

    def can_read(self, func):
        self._can_read = func
        return func

    def can_write(self, func):
        self._can_write = func
        return func

#        for proc in generate_field_procedures(parent._model, field):
#            self._add_child(ProcedureWrapper(proc, self))


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

            if token.user:
                Privilege.grant(token.user, ret, 'MANAGE')

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


Attribute = Struct('Attribute', (
    ('name', str, False),
    ('is_blob', bool, False),
    ('value', str, False),
    ('filename', str, True),
))


def can_attribute_read(token, object):
    return object.demand_right(token, 'ATTRIBUTE_READ')


def can_attribute_write(token, object):
    return object.demand_right(token, 'ATTRIBUTE_WRITE')


class OpenAttributeWrapper(Wrapper):
    def __init__(oaw_self, parent, group_name):
        if group_name is None:
            wrapper_name = 'oa'
        else:
            wrapper_name = group_name

        super(OpenAttributeWrapper, oaw_self).__init__(wrapper_name, parent)
        oaw_self._can_read = can_attribute_read
        oaw_self._can_write = can_attribute_write

        model = parent._model

        def get_group(object):
            if group_name:
                return getattr(object, group_name).attributes
            else:
                return object.attributes

        def oats(oa):
            return {'name': oa.name, 'is_blob': oa.is_blob, 'value': oa.value, 'filename': oa.filename}

        @oaw_self.method
        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @ReturnValue(type=(Attribute, NoneType))
        def get(token, self, name):
            return oats(get_group(self).oa_get(name))

        @oaw_self.method
        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @ReturnValue(type=str)
        def get_str(token, self, name):
            return get_group(self).oa_get_str(name)

        @oaw_self.method
        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @ReturnValue(type=str)
        def get_blob(token, self, name):
            raise Exception('Not implemented')

        @oaw_self.method
        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @ReturnValue(type=str)
        def get_blob_hash(token, self, name):
            return get_group(self).oa_get_blob_hash(name)

        @oaw_self.method
        @Argument('token', type=Token)
        @Argument('self', type=model)
        @ReturnValue(type=TypedList(Attribute))
        def get_list(token, self):
            return [oats(x) for x in get_group(self).all()]

        @oaw_self.method
        @Argument('token', type=Token)
        @Argument('self', type=model)
        @ReturnValue(type=TypedMap(unicode, Attribute))
        def get_map(token, self):
            ret = {}
            for oa in get_group(self).all():
            	ret[oa.name] = oats(oa)
            return ret

        @oaw_self.method
        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('value', type=Attribute)
        @ReturnValue(type=NoneType)
        def set(token, self, value):
            get_group(self).oa_set(value.name, value)

        @oaw_self.method
        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @Argument('value', type=str)
        @ReturnValue(type=NoneType)
        def set_str(token, self, name, value):
            get_group(self).oa_set_str(name, value)
        
        @oaw_self.method
        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @Argument('value', type=str)
        @ReturnValue(type=NoneType)
        def set_blob(token, self, name, value):
            raise Exception('Not implemented.')

        @oaw_self.method
        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @Argument('value', type=str)
        @Argument('filename', type=str)
        @ReturnValue(type=NoneType)
        def set_blob_hash(token, self, name, value, filename=''):
            get_group(self).oa_set_blob_hash(name, value, filename)

        @oaw_self.method
        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('attributes', type=TypedList(Attribute))
        @ReturnValue(type=NoneType)
        def set_list(token, self, attributes):
            g = get_group(self)
            for struct in attributes:
                g.oa_set(struct.name, struct)

        @oaw_self.method
        @Argument('token', type=Token)
        @Argument('self', type=model)
        @Argument('name', type=str)
        @ReturnValue(type=NoneType)
        def delete(token, self, name):
            get_group(self).delete(name)

        @oaw_self.get.can
        @oaw_self.get_str.can
        @oaw_self.get_blob.can
        @oaw_self.get_blob_hash.can
        @oaw_self.get_list.can
        def wrap_can_read(token, self, *args, **kwargs):
            return oaw_self._can_read(token, self)

        @oaw_self.set.can
        @oaw_self.set_str.can
        @oaw_self.set_blob.can
        @oaw_self.set_blob_hash.can
        @oaw_self.set_list.can
        @oaw_self.delete.can
        def wrap_can_write(token, self, *args, **kwargs):
            return oaw_self._can_read(token, self)

    def can_read(self, func):
        self._can_read = func
        return func

    def can_write(self, func):
        self._can_write = func
        return func

    def method(self, proc):
        self._add_child(ProcedureWrapper(proc, self))


class ModelWrapperClass(StaticWrapper):
    def __init__(self, model):
        if len(model._meta.parents) > 1:
            raise Exception('Wrappers don\'t support models with multiple bases.')

        base_wrapper = None
        if model._meta.parents:
            base_wrapper = ModelWrapper(model._meta.parents.keys()[0])

        super(ModelWrapperClass, self).__init__(model._meta.object_name, base_wrapper)
        self._model = model
        
        for field in model._meta.fields:
            if field in model._meta.local_fields:
                self._add_child(FieldWrapper(field, self))
            else:
                self._add_child(getattr(base_wrapper, field.name))

        self._add_child(FilterWrapper(self))
        self._add_child(GetStructWrapper(self))
        self._add_child(SetStructWrapper(self))
        self._add_child(CreateWrapper(self))
        self._add_child(DeleteWrapper(self))

    def attributes(self, name=None):
        self._add_child(OpenAttributeWrapper(self, name))


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
    def process_request(self, proc, args, kwargs):
        """Enters transaction management"""
        print 'tenter'
        transaction.enter_transaction_management()
        transaction.managed(True)

    def process_exception(self, proc, args, kwargs, exception):
        """Rolls back the database and leaves transaction management"""
        print 'trollback'
        if transaction.is_dirty():
            transaction.rollback()
        transaction.leave_transaction_management()
        from django.db import connection
        print connection.queries

    def process_response(self, proc, args, kwargs, ret):
        """Commits and leaves transaction management."""
        print 'tcommit'
        if transaction.is_managed():
            if transaction.is_dirty():
                transaction.commit()
            transaction.leave_transaction_management()
        from django.db import connection
        print connection.queries
        return ret


class TokenVerifyMiddleware(object):
    def process_request(self, proc, args, kwargs):
        if proc.parameters and (proc.parameters[0].name == 'token'):
            if args:
                token = args[0]
            else:
                token = kwargs['token']

            token = Token(token)

            if not token.valid:
                raise Exception('The provided token has expired')

            if token.user_id:
                userid = int(token.user_id)
            else:
                userid = -2
        else:
            userid = -2

        cursor = connection.cursor()
        cursor.callproc('set_user_id', [userid])
        cursor.close()


    def process_exception(self, proc, args, kwargs, exception):
        pass

    def process_response(self, proc, args, kwargs, ret):
        return ret


class CheckRightsMiddleware(object):
    @DispatchOn(type=ArsList)
    def check(self, token, type, value):
        for elem in value:
            self.check(token, type.element_type, elem)

    @DispatchOn(type=ArsSet)
    def check(self, token, type, value):
        for elem in value:
            self.check(token, type.element_type, elem)

    @DispatchOn(type=ArsMap)
    def check(self, token, type, value):
        for (key, elem) in value.iteritems():
            self.check(token, type.key_type, key)
            self.check(token, type.value_type, elem)
    
    @DispatchOn(type=ArsStructure)
    def check(self, token, type, value):
        for field in type.fields:
            if (field.name in value) and (value[field.name] is not None):
                self.check(token, field.type, value[field.name])        

    @DispatchOn(type=ArsAtomicType)
    def check(self, token, type, value):
        pass

    @DispatchOn(type=ArsTypeAlias)
    def check(self, token, type, value):
        self.check(token, type.target_type, value)

    @DispatchOn(type=ArsDjangoModel)
    def check(self, token, type, value):
        if not value.demand_right(token, 'VIEW'):
            raise type.model.DoesNotExist("%s matching query does not exist." % type.model._meta.object_name)

    @DispatchOn(type=ArsList)
    def filter(self, token, type, value):
        if isinstance(type.element_type, ArsDjangoModel):
        	return [elem for elem in value if elem.demand_right(token, 'VIEW')]
        else:
        	return [self.filter(token, type.element_type, elem) for elem in value]

    @DispatchOn(type=ArsSet)
    def filter(self, token, type, value):
        ret = set()
        if isinstance(type.element_type, ArsDjangoModel):
            for elem in set(value):
                if elem.demand_right(token, 'VIEW'):
                    ret.add(elem)
        else:
            for elem in value:
                ret.add(self.filter(token, type.element_type, elem))
        return ret

    @DispatchOn(type=ArsMap)
    def filter(self, token, type, value):
        ret = {}
        if isinstance(type.key_type, ArsDjangoModel) and isinstance(type.value_type, ArsDjangoModel):
            for (key, elem) in value.iteritems():
                if key.demand_right(token, 'VIEW') and elem.demand_right(token, 'VIEW'):
                	ret[key] = value
        elif isinstance(type.key_type, ArsDjangoModel):	
            for (key, elem) in value.iteritems():
                if key.demand_right(token, 'VIEW'):
                	ret[key] = self.filter(token, type.value_type, elem)
        elif isinstance(type.value_type, ArsDjangoModel):	
            for (key, elem) in value.iteritems():
                if elem.demand_right(token, 'VIEW'):
                	ret[self.filter(token, type.key_type, key)] = elem
        else:
            for (key, elem) in value.iteritems():
            	ret[self.filter(token, type.key_type, key)] = self.filter(token, type.value_type, elem)
        return ret
    
    @DispatchOn(type=ArsStructure)
    def filter(self, token, type, value):
        ret = {}
        for field in type.fields:
            if field.name in value:
            	if value[field.name] is None:
            		ret[field.name] = None
                elif isinstance(field.type, ArsDjangoModel):
            		if value[field.name].demand_right(token, 'VIEW'):
            			ret[field.name] = value[field.name]
                    else:
                        # delete the field from structure
                    	pass
                else:
                    ret[field.name] = self.filter(token, field.type, value[field.name])
        return ret

    @DispatchOn(type=ArsAtomicType)
    def filter(self, token, type, value):
        return value

    @DispatchOn(type=ArsTypeAlias)
    def filter(self, token, type, value):
        return self.filter(token, type.target_type, value)

    @DispatchOn(type=ArsDjangoModel)
    def filter(self, token, type, value):
        if value.demand_right(token, 'VIEW'):
        	return value
        else:
            raise Exception('You don\'t have rights to view the returned element.')

    def process_request(self, proc, args, kwargs):
        if proc.parameters and (proc.parameters[0].name == 'token'):
            if args:
                token = args[0]
            else:
                token = kwargs['token']
        else:
            token = Token('')
            
        for i in range(min(len(args), len(proc.parameters))):
            self.check(token, proc.parameters[i].type, args[i])

        for arg_name in kwargs:
            self.check(token, proc.parameters[arg_name].type, kwargs[arg_name])

    def process_exception(self, proc, args, kwargs, exception):
        pass

    def process_response(self, proc, args, kwargs, ret):
        if proc.parameters and (proc.parameters[0].name == 'token'):
            if args:
                token = args[0]
            else:
                token = kwargs['token']
        else:
            token = Token('')
        if ret is None:
        	return ret
        return self.filter(token, proc.return_type, ret)
