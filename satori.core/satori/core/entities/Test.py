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
        cls._inherit_add(inherits, 'MANAGE', 'problem', 'EDIT')
        return inherits

    def save(self, *args, **kwargs):
        self.fixup_data()
        super(Test, self).save(*args, **kwargs)

class TestEvents(Events):
    model = Test
    on_insert = on_update = ['owner', 'problem', 'name']
    on_delete = []
