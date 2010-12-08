# vim:ts=4:sts=4:sw=4:expandtab

from satori.core.export.type_helpers import Struct, DefineException

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
    \"\"\"Attribute group: {1}\"\"\"
    self = self{2}
    try:
        return self.attributes.get(name=name)
    except OpenAttribute.DoesNotExist:
        return None

@ExportMethod(unicode, [DjangoId('{0}'), unicode], PCArg('self', '{3}'))
def {1}_get_str(self, name):
    \"\"\"Attribute group: {1}\"\"\"
    oa = self.{1}_get(name)
    if oa is None:
        return None
    elif oa.is_blob:
        raise BadAttributeType(name=name, required_type='string')
    else:
        return oa.value

@ExportMethod(unicode, [DjangoId('{0}'), unicode], PCArg('self', '{3}'))
def {1}_get_blob(self, name):
    \"\"\"Attribute group: {1}\"\"\"
    oa = self.{1}_get(name)
    if oa is None:
        return None
    elif not oa.is_blob:
        raise BadAttributeType(name=name, required_type='blob')
    return Blob.open(oa.value, oa.filename)

@ExportMethod(unicode, [DjangoId('{0}'), unicode], PCArg('self', '{3}'))
def {1}_get_blob_hash(self, name):
    \"\"\"Attribute group: {1}\"\"\"
    oa = self.{1}_get(name)
    if oa is None:
        return None
    elif not oa.is_blob:
        raise BadAttributeType(name=name, required_type='blob')
    else:
        return oa.value

@ExportMethod(TypedList(Attribute), [DjangoId('{0}')], PCArg('self', '{3}'))
def {1}_get_list(self):
    \"\"\"Attribute group: {1}\"\"\"
    return self{2}.attributes.all()

@ExportMethod(TypedMap(unicode, AnonymousAttribute), [DjangoId('{0}')], PCArg('self', '{3}'))
def {1}_get_map(self):
    \"\"\"Attribute group: {1}\"\"\"
    return dict((oa.name, oa) for oa in self{2}.attributes.all())

@ExportMethod(NoneType, [DjangoId('{0}'), Attribute], PCAnd(PCArg('self', '{4}'), PCRawBlob('value')))
def {1}_set(self, value):
    \"\"\"Attribute group: {1}\"\"\"
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
    \"\"\"Attribute group: {1}\"\"\"
    self.{1}_set(Attribute(name=name, value=value, is_blob=False))

@ExportMethod(NoneType, [DjangoId('{0}'), unicode, int, unicode], PCArg('self', '{4}'))
def {1}_set_blob(self, name, length=-1, filename=''):
    \"\"\"Attribute group: {1}\"\"\"
    def set_hash(hash):
        self.{1}_set(OpenAttribute(name=name, value=hash, filename=filename, is_blob=True))
    return Blob.create(length, set_hash)

@ExportMethod(NoneType, [DjangoId('{0}'), unicode, unicode, unicode], PCAnd(PCArg('self', '{4}'), PCGlobal('RAW_BLOB')))
def {1}_set_blob_hash(self, name, value, filename=''):
    \"\"\"Attribute group: {1}\"\"\"
    self.{1}_set(Attribute(name=name, value=value, filename=filename, is_blob=True))

@ExportMethod(NoneType, [DjangoId('{0}'), TypedList(Attribute)], PCAnd(PCArg('self', '{4}'), PCEach('attributes', PCRawBlob('item'))))
def {1}_add_list(self, attributes):
    \"\"\"Attribute group: {1}\"\"\"
    for struct in attributes:
        self.{1}_set(struct)

@ExportMethod(NoneType, [DjangoId('{0}'), TypedList(Attribute)], PCAnd(PCArg('self', '{4}'), PCEach('attributes', PCRawBlob('item'))))
def {1}_set_list(self, attributes):
    \"\"\"Attribute group: {1}\"\"\"
    self{2}.attributes.all().delete()
    self.{1}_add_list(attributes)

@ExportMethod(NoneType, [DjangoId('{0}'), TypedMap(unicode, AnonymousAttribute)], PCAnd(PCArg('self', '{4}'), PCEachValue('attributes', PCRawBlob('item'))))
def {1}_add_map(self, attributes):
    \"\"\"Attribute group: {1}\"\"\"
    for name, struct in attributes.items():
        struct.name = name
        self.{1}_set(struct)

@ExportMethod(NoneType, [DjangoId('{0}'), TypedMap(unicode, AnonymousAttribute)], PCAnd(PCArg('self', '{4}'), PCEachValue('attributes', PCRawBlob('item'))))
def {1}_set_map(self, attributes):
    \"\"\"Attribute group: {1}\"\"\"
    self{2}.attributes.all().delete()
    self.{1}_add_map(attributes)

@ExportMethod(NoneType, [DjangoId('{0}'), unicode], PCArg('self', '{4}'))
def {1}_delete(self, name):
    \"\"\"Attribute group: {1}\"\"\"
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

    if name is not None:
        exec compile(code_attributegroup_field.format(*format_args), '<oa field code>', 'exec') in global_context, local_context
    
    exec compile(code_attributegroup_methods.format(*format_args), '<oa methods code>', 'exec') in global_context, local_context

