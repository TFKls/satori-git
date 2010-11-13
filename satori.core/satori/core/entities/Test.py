# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev               import Events

from satori.core.models import Entity

@ExportModel
class Test(Entity):
    """Model. Single test.
    """

    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_test')

    problem     = models.ForeignKey('Problem')
    name        = models.CharField(max_length=50)
    description = models.TextField(blank=True, default='')
    environment = models.CharField(max_length=50)
    obsolete    = models.BooleanField(default=False)

    generate_attribute_group('Test', 'data', 'VIEW', 'MANAGE', globals(), locals())

    class ExportMeta(object):
        fields = [('problem', 'VIEW'), ('name', 'VIEW'), ('description', 'VIEW'), ('environment', 'VIEW'), ('obsolete', 'VIEW')]

    def save(self):
        self.fixup_data()

        super(Test, self).save()

    @classmethod
    def inherit_rights(cls):
        inherits = super(Test, cls).inherit_rights()
        cls._inherit_add(inherits, 'MANAGE', 'problem', 'EDIT')
        return inherits

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('problem', 'name'),)

class TestEvents(Events):
    model = Test
    on_insert = on_update = ['owner', 'problem', 'name']
    on_delete = []

