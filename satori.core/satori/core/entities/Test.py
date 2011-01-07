# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class Test(Entity):
    """Model. Single test.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_test')

    problem       = models.ForeignKey('Problem', related_name='tests')
    name          = models.CharField(max_length=50)
    description   = models.TextField(blank=True, default='')
    environment   = models.CharField(max_length=50)
    obsolete      = models.BooleanField(default=False)

    data          = AttributeGroupField(PCArg('self', 'VIEW'), PCArg('self', 'MANAGE'), '')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('problem', 'name'),)

    class ExportMeta(object):
        fields = [('problem', 'VIEW'), ('name', 'VIEW'), ('description', 'VIEW'), ('environment', 'VIEW'), ('obsolete', 'VIEW')]

    @classmethod
    def inherit_rights(cls):
        inherits = super(Test, cls).inherit_rights()
        cls._inherit_add(inherits, 'MANAGE', 'problem', 'MANAGE')
        return inherits

    def save(self, *args, **kwargs):
        self.fixup_data()
        super(Test, self).save(*args, **kwargs)

    @ExportMethod(DjangoStruct('Test'), [DjangoStruct('Test'), TypedMap(unicode, AnonymousAttribute)], PCArgField('fields', 'problem', 'MANAGE'))
    @staticmethod
    def create(fields, data):
        test = Test()
        test.problem = fields.problem
        test.name = fields.name
        test.description = fields.description
        test.environment = fields.environment
        test.save()
        test.data_set_map(data)
        return test

    @ExportMethod(DjangoStruct('Test'), [DjangoId('Test'), DjangoStruct('Test'), TypedMap(unicode, AnonymousAttribute)], PCArg('self', 'MANAGE'))
    def modify(self, fields, data):
        self.name = fields.name
        self.description = fields.description
        self.environment = fields.environment
        self.obsolete = fields.obsolete
        self.save()
        self.data_set_map(data)
        return self

    #@ExportMethod(NoneType, [DjangoId('Test')], PCArg('self', 'MANAGE'), [CannotDeleteObject])
    def delete(self):
        logging.error('test deleted') #TODO: Waiting for non-cascading deletes in django
        self.privileges.all().delete()
        try:
            super(Test, self).delete()
        except DatabaseError:
            raise CannotDeleteObject()

class TestEvents(Events):
    model = Test
    on_insert = on_update = ['owner', 'problem', 'name']
    on_delete = []
