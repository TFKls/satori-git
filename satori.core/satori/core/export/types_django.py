# vim:ts=4:sts=4:sw=4:expandtab

from   datetime  import datetime
from   django.db import models
import inspect

from satori.ars.model import *

from satori.core.export.type_helpers import DefineException, ArsDeferredStructure, python_to_ars_type
from satori.core.export.pc import AccessDenied

ArgumentNotFound = DefineException('ArgumentNotFound', 'The specified argument cannot be found: model={model}, id={id}',
    [('model', unicode, False), ('id', long, False)])


CannotReturnObject = DefineException('CannotReturnObject', 'You don\'t have rights to view the returned object')

CannotDeleteObject = DefineException('CannotDeleteObject', 'You can\'t delete this object')


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
#        # decided not to enforce
#        if not Privilege.demand(value, 'VIEW'):
#            raise CannotReturnObject()

        return value.id

    def do_convert_from_ars(self, value):
        try:
            ret = Privilege.select_can(self.model.objects.all(), 'VIEW').get(id=value)
        except self.model.DoesNotExist:
            raise ArgumentNotFound(model=self.model.__name__, id=value)
        else:
            if not ret._can_VIEW:
                raise AccessDenied()
            return ret


class DjangoId(object):
    def __init__(self, model):
        super(DjangoId, self).__init__()
        self.model = model

    def ars_type(self):
        if not self.model in ars_django_id:
            raise RuntimeError('Model not exported: {0}'.format(self.model))

        return ars_django_id[self.model]


class ArsDjangoStructure(ArsDeferredStructure):
    def __init__(self, model, fields, extra_fields):
        super(ArsDjangoStructure, self).__init__(model.__name__ + 'Struct', [])
        self.model = model
        self.django_fields = fields
        self.django_extra_fields = extra_fields

    def init_fields(self):
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

        for field in self.fields.items:
            if hasattr(ret, field.name) and field.type.needs_conversion():
                if isinstance(field.type, DjangoId):
                    if getattr(ret, field.name + '_id') is None:
                        delattr(ret, field.name)
                    else:
                        logging.debug('field %s type %s', field.name, type(getattr(ret, field.name + '_id')))
                        setattr(ret, field.name, getattr(ret, field.name + '_id'))
                else:
                    setattr(ret, field.name, field.type.convert_to_ars(getattr(ret, field.name)))

            return ret

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
        return super(ArsDjangoIdList, self).do_convert_to_ars(Privilege.select_can(Privilege.where_can(value ,'VIEW'), 'VIEW'))

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
        return super(ArsDjangoStructureList, self).do_convert_to_ars(Privilege.select_struct_can(Privilege.where_can(value ,'VIEW')))

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


def generate_django_types(cls):
    ars_django_id[cls] = ArsDjangoId(cls)
    ars_django_id[cls.__name__] = ars_django_id[cls]

    fields = []
    extra_fields = []

    for parent_cls in reversed(inspect.getmro(cls)):
        if 'ExportMeta' in parent_cls.__dict__:
            if hasattr(parent_cls.ExportMeta, 'fields'):
                fields.extend(parent_cls.ExportMeta.fields)
            if hasattr(parent_cls.ExportMeta, 'extra_fields'):
                extra_fields.extend(parent_cls.ExportMeta.extra_fields)

    ars_django_structure[cls] = ArsDjangoStructure(cls, fields, extra_fields)
    ars_django_structure[cls.__name__] = ars_django_structure[cls]

    ars_django_id_list[cls] = ArsDjangoIdList(cls)
    ars_django_id_list[cls.__name__] = ars_django_id_list[cls]

    ars_django_structure_list[cls] = ArsDjangoStructureList(cls)
    ars_django_structure_list[cls.__name__] = ars_django_structure_list[cls]

    cls._struct_rights = set([field_permission for (field_name, field_permission) in fields]
            + [field_permission for (field_name, field_type, field_permission) in extra_fields]
            + ['VIEW'])

def init():
    global Privilege
    from satori.core.models import Privilege

