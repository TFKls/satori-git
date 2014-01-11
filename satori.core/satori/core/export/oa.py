# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import sys

from satori.core.export.docstring    import trim_docstring
from satori.core.export.type_helpers import Struct, DefineException

BadAttributeType = DefineException('BadAttributeType', 'The requested attribute "{name}" is not a {requested_type} attribute',
    [('name', unicode, False), ('requested_type', unicode, False)])
MissingBlob = DefineException('MissingBlob', 'The requested blob does not exist', [])

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


code_attributegroup_fixup = """
def fixup_{1}(self):
    pass
#    try:
#        x = self.{1}
#    except AttributeGroup.DoesNotExist:
#        {1} = AttributeGroup()
#        {1}.save()
#        self.{1} = {1}
"""


code_attributegroup_methods = """
@ExportMethod(Attribute, [DjangoId('{0}'), unicode], pc_read)
def {1}_get(self, name):
    \"\"\"Attribute group: {1}\"\"\"
    self = self{2}
    try:
        return self.attributes.get(name=name)
    except OpenAttribute.DoesNotExist:
        return None

@ExportMethod(unicode, [DjangoId('{0}'), unicode, unicode], pc_read, [BadAttributeType])
def {1}_get_str(self, name, fallback=None):
    \"\"\"Attribute group: {1}\"\"\"
    oa = self.{1}_get(name)
    if oa is None:
        return fallback
    elif oa.is_blob:
        raise BadAttributeType(name=name, requested_type='string')
    else:
        return oa.value

@ExportMethod(unicode, [DjangoId('{0}'), unicode], pc_read, [BadAttributeType])
def {1}_get_blob(self, name):
    \"\"\"Attribute group: {1}\"\"\"
    oa = self.{1}_get(name)
    if oa is None:
        return None
    elif not oa.is_blob:
        raise BadAttributeType(name=name, requested_type='blob')
    return Blob.open(oa.value, oa.filename)

@ExportMethod(unicode, [DjangoId('{0}'), unicode], pc_read, [BadAttributeType])
def {1}_get_blob_hash(self, name):
    \"\"\"Attribute group: {1}\"\"\"
    oa = self.{1}_get(name)
    if oa is None:
        return None
    elif not oa.is_blob:
        raise BadAttributeType(name=name, requested_type='blob')
    else:
        return oa.value

@ExportMethod(TypedList(Attribute), [DjangoId('{0}')], pc_read)
def {1}_get_list(self):
    \"\"\"Attribute group: {1}\"\"\"
    return self{2}.attributes.all()

@ExportMethod(TypedMap(unicode, AnonymousAttribute), [DjangoId('{0}')], pc_read)
def {1}_get_map(self):
    \"\"\"Attribute group: {1}\"\"\"
    return dict((oa.name, oa) for oa in self{2}.attributes.all())

@ExportMethod(NoneType, [DjangoId('{0}'), Attribute], PCAnd(pc_write, PCRawBlob('value')), [MissingBlob])
def {1}_set(self, value):
    \"\"\"Attribute group: {1}\"\"\"
    self = self{2}
    if value.is_blob and not Blob.exists(value.value):
        raise MissingBlob()
    (newoa, created) = self.attributes.get_or_create(name=value.name)
    newoa.is_blob = value.is_blob
    newoa.value = value.value
    if value.is_blob and hasattr(value, 'filename') and value.filename is not None:
        newoa.filename = value.filename
    else:
        newoa.filename = ''
    newoa.save()

@ExportMethod(NoneType, [DjangoId('{0}'), unicode, unicode], pc_write)
def {1}_set_str(self, name, value):
    \"\"\"Attribute group: {1}\"\"\"
    self.{1}_set(Attribute(name=name, value=value, is_blob=False))

@ExportMethod(NoneType, [DjangoId('{0}'), unicode, int, unicode], pc_write)
def {1}_set_blob(self, name, length=-1, filename=''):
    \"\"\"Attribute group: {1}\"\"\"
    def set_hash(hash):
        self.{1}_set(OpenAttribute(name=name, value=hash, filename=filename, is_blob=True))
    return Blob.create(length, set_hash)

@ExportMethod(NoneType, [DjangoId('{0}'), unicode, unicode, unicode], PCAnd(pc_write, PCGlobal('RAW_BLOB')), [MissingBlob])
def {1}_set_blob_hash(self, name, value, filename=''):
    \"\"\"Attribute group: {1}\"\"\"
    self.{1}_set(Attribute(name=name, value=value, filename=filename, is_blob=True))

@ExportMethod(NoneType, [DjangoId('{0}'), TypedList(Attribute)], PCAnd(pc_write, PCEach('attributes', PCRawBlob('item'))), [MissingBlob])
def {1}_add_list(self, attributes):
    \"\"\"Attribute group: {1}\"\"\"
    for struct in attributes:
        self.{1}_set(struct)

@ExportMethod(NoneType, [DjangoId('{0}'), TypedList(Attribute)], PCAnd(pc_write, PCEach('attributes', PCRawBlob('item'))), [MissingBlob])
def {1}_set_list(self, attributes):
    \"\"\"Attribute group: {1}\"\"\"
    self{2}.attributes.all().delete()
    self.{1}_add_list(attributes)

@ExportMethod(NoneType, [DjangoId('{0}'), TypedMap(unicode, AnonymousAttribute)], PCAnd(pc_write, PCEachValue('attributes', PCRawBlob('item'))), [MissingBlob])
def {1}_add_map(self, attributes):
    \"\"\"Attribute group: {1}\"\"\"
    for name, struct in attributes.items():
        struct.name = name
        self.{1}_set(struct)

@ExportMethod(NoneType, [DjangoId('{0}'), TypedMap(unicode, AnonymousAttribute)], PCAnd(pc_write, PCEachValue('attributes', PCRawBlob('item'))), [MissingBlob])
def {1}_set_map(self, attributes):
    \"\"\"Attribute group: {1}\"\"\"
    self{2}.attributes.all().delete()
    self.{1}_add_map(attributes)

@ExportMethod(NoneType, [DjangoId('{0}'), unicode], pc_write)
def {1}_delete(self, name):
    \"\"\"Attribute group: {1}\"\"\"
    oa = self.{1}_get(name)
    if oa is not None:
        oa.delete()
"""

docstrings_to_append = []

class DefaultAttributeGroupField(object):
    def __init__(self, pc_read, pc_write, doc):
        self.doc = doc
        self.pc_read = pc_read
        self.pc_write = pc_write

    def contribute_to_class(self, cls, name):
        global_dict = sys.modules['satori.core.models'].__dict__
        local_dict = {'pc_read': self.pc_read, 'pc_write': self.pc_write}

        exec compile(code_attributegroup_methods.format(cls.__name__, name, ''), '<oa methods code>', 'exec') in global_dict, local_dict

        del local_dict['pc_read']
        del local_dict['pc_write']
       
        for (meth_name, meth) in local_dict.items():
            setattr(cls, meth_name, meth)

        docstrings_to_append.append((cls, name, self.doc))


class AttributeGroupField(models.OneToOneField):
    def __init__(self, pc_read, pc_write, doc):
        super(AttributeGroupField, self).__init__('AttributeGroup', related_name='+', on_delete=models.CASCADE)
        self.doc = doc
        self.pc_read = pc_read
        self.pc_write = pc_write

    def contribute_to_class(self, cls, name):
        super(AttributeGroupField, self).contribute_to_class(cls, name)
        
        global_dict = sys.modules['satori.core.models'].__dict__
        local_dict = {'pc_read': self.pc_read, 'pc_write': self.pc_write}

        exec compile(code_attributegroup_methods.format(cls.__name__, name, '.' + name), '<oa methods code>', 'exec') in global_dict, local_dict
        exec compile(code_attributegroup_fixup.format(cls.__name__, name, '.' + name), '<oa methods code>', 'exec') in global_dict, local_dict

        del local_dict['pc_read']
        del local_dict['pc_write']

        for (meth_name, meth) in local_dict.items():
            setattr(cls, meth_name, meth)
        
        docstrings_to_append.append((cls, name, self.doc))

        @receiver(post_save, sender=cls, weak=False)
        def update_refs(sender, instance, created, **kwargs):
            if created:
                oag = getattr(instance, self.name)
                oag.enclosing_entity = instance
                oag.save()

    def pre_save(self, model_instance, add):
        if add:
            ag = AttributeGroup()
            ag.save()
            setattr(model_instance, self.name, ag)
        return super(AttributeGroupField, self).pre_save(model_instance, add)

# bad, because installed after post_syncdb signal:

#    def post_create_sql(self, style, table_name):
#        trigger = """
#CREATE FUNCTION fixup_oagroup_{0}_{1}() RETURNS trigger AS $$
#    BEGIN
#        UPDATE core_attributegroup SET enclosing_entity_id = NEW.{2} WHERE parent_entity_id = NEW.{1};
#        RETURN NEW;
#    END;
#$$ LANGUAGE plpgsql;
#
#CREATE TRIGGER fixup_oagroup_{0}_{1} AFTER INSERT ON {0} FOR EACH ROW EXECUTE PROCEDURE fixup_oagroup_{0}_{1}();
#""".format(table_name, self.column, self.model._meta.pk.column)
#        return [trigger]


def init():
    global AttributeGroup
    from satori.core.models import AttributeGroup

    for (cls, name, docstring) in docstrings_to_append:
        doc = trim_docstring(cls.__doc__)
        if doc:
            doc = doc + '\n\n'
        
        if doc.find('Attribute groups:') == -1:
            doc = doc + 'Attribute groups:\n\n'

        doc = doc + '  .. ars:attributegroup:: {0}\n\n    {1}'.format(name, docstring)
        cls.__doc__ = doc

