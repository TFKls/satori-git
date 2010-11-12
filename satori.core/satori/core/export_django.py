# vim:ts=4:sts=4:sw=4:expandtab

from datetime import datetime
from django.db import models
import inspect
from types import NoneType

from satori.ars.model import *
from satori.core.export import ExportClass, ExportMethod, global_exception_types, Struct, DefineException, PCPermit, PCArg,  python_to_ars_type, token_container


ArgumentNotFound = DefineException('ArgumentNotFound', 'The specified argument cannot be found: model={model}, id={id}',
    [('model', unicode, False), ('id', long, False)])

global_exception_types.append(ArgumentNotFound)

CannotReturnObject = DefineException('CannotReturnObject', 'You don\'t have rights to view the returned object')

global_exception_types.append(CannotReturnObject)

field_basic_types = {
    models.AutoField: long,
    models.IntegerField: int,
    models.CharField: unicode,
    models.TextField: unicode,
    models.BooleanField: bool,
    models.DateTimeField: datetime,
    models.IPAddressField: unicode,
}


field_type_map = {}

def django_field_to_python_type(field):
    if not field in field_type_map:
        field_type = None
        if type(field) in field_basic_types:
            field_type = field_basic_types[type(field)]
        if isinstance(field, models.ForeignKey):
            if issubclass(field.rel.to, models.Model):
                field_type = DjangoId(field.rel.to.__name__)
            else:
                field_type = DjangoId(field.rel.to.split('.')[-1])
        field_type_map[field] = field_type

    return field_type_map[field]


ars_django_id = {}
ars_django_structure = {}
ars_django_id_list = {}
ars_django_structure_list = {}

class ArsDjangoId(ArsTypeAlias):
    def __init__(self, model):
        super(ArsDjangoId, self).__init__(name=(model.__name__ + 'Id'), target_type=ArsInt64)
        self.model = model

    def do_needs_conversion(self):
        return True

    def do_convert_to_ars(self, value):
        if not Privilege.demand(value, 'VIEW'):
            raise CannotReturnObject()

        return value.id

    def do_convert_from_ars(self, value):
        try:
            return self.model.objects.extra(where=['right_check(id, %s)'], params=['VIEW']).get(id=value)
        except model.DoesNotExist:
            raise ArgumentNotFound(model=self.model.__name__, id=value)


class DjangoId(object):
    def __init__(self, model):
        super(DjangoId, self).__init__()
        self.model = model

    def ars_type(self):
        if not self.model in ars_django_id:
            raise RuntimeError('Model not exported: {0}'.format(self.model))

        return ars_django_id[self.model]


class ArsDjangoStructure(ArsStructure):
    def __init__(self, model, fields, extra_fields):
        super(ArsDjangoStructure, self).__init__(name=(model.__name__ + 'Struct'))
        self.model = model
        self.django_fields = fields
        self.django_extra_fields = extra_fields

        self._fields_generated = False

    def _generate_fields(self):
        if self._fields_generated:
            return

        self._fields_generated = True

        field_dict = dict((field.name, field) for field in self.model._meta.fields)
    
        for (field_name, field_permission) in self.django_fields:
            self.add_field(name=field_name, type=python_to_ars_type(django_field_to_python_type(field_dict[field_name])), optional=True)

        for (field_name, field_type, field_permission) in self.django_extra_fields:
            self.add_field(name=field_name, type=python_to_ars_type(field_type), optional=True)

    def do_needs_conversion(self):
        return True

    def do_convert_to_ars(self, value):
        if not Privilege.demand(value, 'VIEW'):
            raise CannotReturnObject()

        ret = self.get_class()()

        for (field_name, field_permission) in self.django_fields:
            if Privilege.demand(value, field_permission):
                setattr(ret, field_name, getattr(value, field_name))

        for (field_name, field_type, field_permission) in self.django_extra_fields:
            if Privilege.demand(value, field_permission):
                setattr(ret, field_name, getattr(value, field_name))

        return super(ArsDjangoStructure, self).do_convert_to_ars(ret)

    def do_convert_from_ars(self, value):
        return super(ArsDjangoStructure, self).do_convert_from_ars(value)


class DjangoStruct(object):
    def __init__(self, model):
        super(DjangoStruct, self).__init__()
        self.model = model

    def __call__(self, *args, **kwargs):
        return self.ars_type().get_class()(*args, **kwargs)

    def ars_type(self):
        if not self.model in ars_django_structure:
            raise RuntimeError('Model not exported: {0}'.format(self.model))

        return ars_django_structure[self.model]


class ArsDjangoIdList(ArsList):
    def __init__(self, model):
        super(ArsDjangoIdList, self).__init__(element_type=ars_django_id[model])
        self.model = model

    def do_needs_conversion(self):
        return True

    def do_convert_to_ars(self, value):
        return super(ArsDjangoIdList, self).do_convert_to_ars(value.extra(where=['right_check(id, %s)'], params=['VIEW']))

    def do_convert_from_ars(self, value):
        return super(ArsDjangoIdList, self).do_convert_from_ars(value)


class DjangoIdList(object):
    def __init__(self, model):
        super(DjangoIdList, self).__init__()
        self.model = model

    def ars_type(self):
        if not self.model in ars_django_id_list:
            raise RuntimeError('Model not exported: {0}'.format(self.model))

        return ars_django_id_list[self.model]


class ArsDjangoStructureList(ArsList):
    def __init__(self, model):
        super(ArsDjangoStructureList, self).__init__(element_type=ars_django_structure[model])
        self.model = model

    def do_needs_conversion(self):
        return True

    def do_convert_to_ars(self, value):
        return super(ArsDjangoStructureList, self).do_convert_to_ars(value.extra(where=['right_check(id, %s)'], params=['VIEW']))

    def do_convert_from_ars(self, value):
        return super(ArsDjangoStructureList, self).do_convert_from_ars(value)


class DjangoStructList(object):
    def __init__(self, model):
        super(DjangoStructList, self).__init__()
        self.model = model

    def ars_type(self):
        if not self.model in ars_django_structure_list:
            raise RuntimeError('Model not exported: {0}'.format(self.model))

        return ars_django_structure_list[self.model]

def generate_all_fields():
    for (name, struct) in ars_django_structure.items():
        struct._generate_fields()

def ExportModel(cls):
    ars_django_id[cls] = ArsDjangoId(cls)
    ars_django_id[cls.__name__] = ars_django_id[cls]

    fields = []
    extra_fields = []

    for parent_cls in reversed(inspect.getmro(cls)):
        if 'ExportMeta' in parent_cls.__dict__:
            if hasattr(parent_cls.ExportMeta, 'fields'):
                fields.extend(parent_cls.ExportMeta.fields)
            if hasattr(parent_cls.ExportMeta, 'extra_fields'):
                fields.extend(parent_cls.ExportMeta.extra_fields)

    ars_django_structure[cls] = ArsDjangoStructure(cls, fields, extra_fields)
    ars_django_structure[cls.__name__] = ars_django_structure[cls]

    ars_django_id_list[cls] = ArsDjangoIdList(cls)
    ars_django_id_list[cls.__name__] = ars_django_id_list[cls]

    ars_django_structure_list[cls] = ArsDjangoStructureList(cls)
    ars_django_structure_list[cls.__name__] = ars_django_structure_list[cls]

    @ExportMethod(DjangoStruct(cls), [DjangoId(cls)], PCPermit())
    def get_struct(self):
        return self

    cls.get_struct = get_struct

    @ExportMethod(DjangoStruct(cls), [DjangoId(cls), DjangoStruct(cls)], PCArg('self', 'MANAGE'))
    def set_struct(self, arg_struct):
        for (field_name, field_permission) in ars_django_structure[cls].django_fields:
            if field_name != 'id':
                if hasattr(arg_struct, field_name) and (getattr(arg_struct, field_name) is not None):
                    setattr(self, getattr(arg_struct, field_name))
        self.save()
        return self

    cls.set_struct = set_struct

    @ExportMethod(DjangoStructList(cls), [DjangoStruct(cls)], PCPermit())
    @staticmethod
    def filter(arg_struct=None):
        kwargs = {}
        for (field_name, field_permission) in ars_django_structure[cls].django_fields:
            if hasattr(arg_struct, field_name) and (getattr(arg_struct, field_name) is not None):
                kwargs[field_name] = getattr(arg_struct, field_name)
        return cls.objects.filter(**kwargs)

    cls.filter = filter

    if not 'create' in cls.__dict__:
        @ExportMethod(DjangoStruct(cls), [DjangoStruct(cls)], PCPermit())
        @staticmethod
        def create(arg_struct):
            kwargs = {}
            for (field_name, field_permission) in ars_django_structure[cls].django_fields:
                if hasattr(arg_struct, field_name) and (getattr(arg_struct, field_name) is not None):
                    kwargs[field_name] = getattr(arg_struct, field_name)
            obj = cls(**kwargs)
            obj.save()
            if token_container.token.user:
                Privilege.grant(token_container.token.user, obj, 'MANAGE')
            return obj

        cls.create = create

    if not 'delete' in cls.__dict__:
        @ExportMethod(NoneType, [DjangoId(cls)], PCArg('self', 'MANAGE'))
        def delete(self):
            super(cls, self).delete()

        cls.delete = delete

    return ExportClass(cls)


BadAttributeType = DefineException('BadAttributeType', 'The requested attribute "{name}" is not a {requested_type} attribute',
    [('name', unicode, False), ('requested_type', unicode, False)])

Attribute = Struct('Attribute', (
    ('name', str, False),
    ('is_blob', bool, False),
    ('value', str, False),
    ('filename', str, True),
))


AnonymousAttribute = Struct('AnonymousAttribute', (
    ('is_blob', bool, False),
    ('value', str, False),
    ('name', str, True),
    ('filename', str, True),
))


class PCRawBlob(object):
    def __init__(__pc__self, name):
        super(PCRawBlob, __pc__self).__init__()
        __pc__self.name = name

    def __call__(__pc__self, **kwargs):
        if kwargs[__pc__self.name].is_blob:
            return Privilege.global_demand('RAW_BLOB')
        else:
            return True

    def __str__(__pc__self):
        return 'global RAW_BLOB if {0}.is_blob = True'.format(__pc__self.name)


code_attributegroup_imports = """
from types import NoneType
from django.db import models
from satori.core.export import TypedList, TypedMap, PCAnd, PCEach, PCEachValue, PCArg, PCGlobal
from satori.core.export_django import DjangoId, Attribute, AnonymousAttribute, BadAttributeType, PCRawBlob
"""


code_attributegroup_field = """
{1} = models.OneToOneField('AttributeGroup', related_name='group_{0}_{1}')
def fixup_{1}(self):
    try:
        x = self.{1}
    except AttributeGroup.DoesNotExist:
        {1} = AttributeGroup()
        {1}.save()
        self.{1} = {1}
"""


code_attributegroup_methods = """
@ExportMethod(Attribute, [DjangoId('{0}'), unicode], PCArg('self', '{3}'))
def {1}_get(self, name):
    self = self{2}
    try:
        return self.attributes.get(name=name)
    except OpenAttribute.DoesNotExist:
        return None

@ExportMethod(unicode, [DjangoId('{0}'), unicode], PCArg('self', '{3}'))
def {1}_get_str(self, name):
    oa = self.{1}_get(name)
    if oa is None:
        return None
    elif oa.is_blob:
        raise BadAttributeType(name=name, required_type='string')
    else:
        return oa.value

@ExportMethod(unicode, [DjangoId('{0}'), unicode], PCArg('self', '{3}'))
def {1}_get_blob(self, name):
    oa = self.{1}_get(name)
    if oa is None:
        return None
    elif not oa.is_blob:
        raise BadAttributeType(name=name, required_type='blob')
    return Blob.open(oa.value, oa.filename)

@ExportMethod(unicode, [DjangoId('{0}'), unicode], PCArg('self', '{3}'))
def {1}_get_blob_hash(self, name):
    oa = self.{1}_get(name)
    if oa is None:
        return None
    elif not oa.is_blob:
        raise BadAttributeType(name=name, required_type='blob')
    else:
        return oa.value

@ExportMethod(TypedList(Attribute), [DjangoId('{0}')], PCArg('self', '{3}'))
def {1}_get_list(self):
    return self{2}.attributes.all()

@ExportMethod(TypedMap(unicode, AnonymousAttribute), [DjangoId('{0}')], PCArg('self', '{3}'))
def {1}_get_map(self):
    return dict((oa.name, oa) for oa in self{2}.attributes.all())

@ExportMethod(NoneType, [DjangoId('{0}'), Attribute], PCAnd(PCArg('self', '{4}'), PCRawBlob('value')))
def {1}_set(self, value):
    self = self{2}
    (newoa, created) = self.attributes.get_or_create(name=value.name)
    newoa.is_blob = value.is_blob
    newoa.value = value.value
    if value.is_blob and hasattr(value, 'filename') and value.filename is not None:
        newoa.filename = value.filename
    else:
        newoa.filename = ''
    newoa.save()

@ExportMethod(NoneType, [DjangoId('{0}'), unicode, unicode], PCArg('self', '{4}'))
def {1}_set_str(self, name, value):
    self.{1}_set(Attribute(name=name, value=value, is_blob=False))

@ExportMethod(NoneType, [DjangoId('{0}'), unicode, int, unicode], PCArg('self', '{4}'))
def {1}_set_blob(self, name, length=-1, filename=''):
    def set_hash(hash):
        self.{1}_set(OpenAttribute(name=name, value=hash, filename=filename, is_blob=True))
    return Blob.create(length, set_hash)

@ExportMethod(NoneType, [DjangoId('{0}'), unicode, unicode, unicode], PCAnd(PCArg('self', '{4}'), PCGlobal('RAW_BLOB')))
def {1}_set_blob_hash(self, name, value, filename=''):
    self.{1}_set(Attribute(name=name, value=value, filename=filename, is_blob=True))

@ExportMethod(NoneType, [DjangoId('{0}'), TypedList(Attribute)], PCAnd(PCArg('self', '{4}'), PCEach('attributes', PCRawBlob('item'))))
def {1}_add_list(self, attributes):
    for struct in attributes:
        self.{1}_set(struct)

@ExportMethod(NoneType, [DjangoId('{0}'), TypedList(Attribute)], PCAnd(PCArg('self', '{4}'), PCEach('attributes', PCRawBlob('item'))))
def {1}_set_list(self, attributes):
    self{2}.attributes.all().delete()
    self.{1}_add_list(attributes)

@ExportMethod(NoneType, [DjangoId('{0}'), TypedMap(unicode, AnonymousAttribute)], PCAnd(PCArg('self', '{4}'), PCEachValue('attributes', PCRawBlob('item'))))
def {1}_add_map(self, attributes):
    for name, struct in attributes.items():
        struct.name = name
        self.{1}_set(struct)

@ExportMethod(NoneType, [DjangoId('{0}'), TypedMap(unicode, AnonymousAttribute)], PCAnd(PCArg('self', '{4}'), PCEachValue('attributes', PCRawBlob('item'))))
def {1}_set_map(self, attributes):
    self{2}.attributes.all().delete()
    self.{1}_add_map(attributes)

@ExportMethod(NoneType, [DjangoId('{0}'), unicode], PCArg('self', '{4}'))
def {1}_delete(self, name):
    oa = self.{1}_get(name)
    if oa is not None:
        oa.delete()
"""


def generate_attribute_group(model_name, name, read_permission, write_permission, global_context, local_context):
    if name is None:
        name_prefix = 'oa'
        group_code = ''
    else:
        name_prefix = name
        group_code = '.' + name

    format_args = (model_name, name_prefix, group_code, read_permission, write_permission)

    exec compile(code_attributegroup_imports.format(*format_args), '<oa import code>', 'exec') in global_context, global_context

    if name is not None:
        exec compile(code_attributegroup_field.format(*format_args), '<oa field code>', 'exec') in global_context, local_context
    
    exec compile(code_attributegroup_methods.format(*format_args), '<oa methods code>', 'exec') in global_context, local_context

