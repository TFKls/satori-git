# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class Test(Entity):
    """Model. Single test.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_test')

    problem       = models.ForeignKey('Problem', related_name='tests', on_delete=models.CASCADE)
    name          = models.CharField(max_length=64)
    description   = models.TextField(blank=True, default='')
    environment   = models.CharField(max_length=64)
    obsolete      = models.BooleanField(default=False)

    data          = AttributeGroupField(PCArg('self', 'VIEW'), PCDeny(), '')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('problem', 'name'),)

    class ExportMeta(object):
        fields = [('problem', 'VIEW'), ('name', 'VIEW'), ('description', 'VIEW'), ('environment', 'VIEW'), ('obsolete', 'VIEW')]
    
    class RightsMeta(object):
        inherit_parent = 'problem'
        inherit_parent_require = 'VIEW'

        inherit_parent_MANAGE = ['MANAGE']

    @classmethod
    def inherit_rights(cls):
        inherits = super(Test, cls).inherit_rights()
        cls._inherit_add(inherits, 'MANAGE', 'problem', 'MANAGE')
        return inherits

    def save(self, *args, **kwargs):
        self.fixup_data()
        super(Test, self).save(*args, **kwargs)

    @ExportMethod(DjangoStruct('Test'), [DjangoStruct('Test'), TypedMap(unicode, AnonymousAttribute)], PCAnd(PCArgField('fields', 'problem', 'MANAGE'), PCEachValue('data', PCRawBlob('item'))), [CannotSetField])
    @staticmethod
    def create(fields, data):
        test = Test()
        test.forbid_fields(fields, ['id', 'obsolete'])
        test.update_fields(fields, ['problem', 'name', 'description', 'environment'])
        test.save()
        test.data_set_map(data)
        return test

    @ExportMethod(DjangoStruct('Test'), [DjangoId('Test'), DjangoStruct('Test')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, ['id', 'problem', 'environment'])
        self.update_fields(fields, ['name', 'description', 'obsolete'])
        self.save()
        return self

    @ExportMethod(DjangoStruct('Test'), [DjangoId('Test'), DjangoStruct('Test'), TypedMap(unicode, AnonymousAttribute)], PCAnd(PCArg('self', 'MANAGE'), PCEachValue('data', PCRawBlob('item'))), [CannotSetField])
    def modify_full(self, fields, data):
        self.forbid_fields(fields, ['id', 'problem'])
        self.update_fields(fields, ['name', 'description', 'environment', 'obsolete'])
        self.save()
        self.data_set_map(data)
        self.rejudge()
        return self

    @ExportMethod(NoneType, [DjangoId('Test')], PCArg('self', 'MANAGE'), [CannotDeleteObject])
    def delete(self):
        try:
            super(Test, self).delete()
        except models.ProtectedError as e:
            raise CannotDeleteObject()

    @ExportMethod(NoneType, [DjangoId('Test')], PCArg('self', 'MANAGE'))
    def rejudge(self):
        RawEvent().send(Event(type='checking_rejudge_test', id=self.id))


class TestEvents(Events):
    model = Test
    on_insert = on_update = ['owner', 'problem', 'name']
    on_delete = []
