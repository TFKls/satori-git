# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

#@ExportModel
class TestMapping(Entity):
    """Model. Intermediary for many-to-many relationship between TestSuites and
    Tests.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_testmapping')

    suite         = models.ForeignKey('TestSuite', related_name='test_mappings+')
    test          = models.ForeignKey('Test', related_name='test_mappings+')
    order         = models.IntegerField()

    params        = AttributeGroupField(PCArg('self', 'MANAGE'), PCDeny(), '')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('suite', 'test'), ('suite', 'order'))
        ordering        = ('order',)

#    class ExportMeta(object):
#        fields = [('suite', 'VIEW'), ('test', 'VIEW'), ('order', 'VIEW')]

    def save(self, *args, **kwargs):
        self.fixup_params()
        super(TestMapping, self).save(*args, **kwargs)

class TestMappingEvents(Events):
    model = TestMapping
    on_insert = on_update = ['suite', 'test']
    on_delete = []
