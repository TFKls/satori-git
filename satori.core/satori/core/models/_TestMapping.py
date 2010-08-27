# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import Events
from satori.core.models._Object import Object

class TestMapping(Object):
    """Model. Intermediary for many-to-many relationship between TestSuites and
    Tests.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_testmapping')

    suite       = models.ForeignKey('TestSuite')
    test        = models.ForeignKey('Test')
    order       = models.IntegerField()
    
    def __str__(self):
        return self.order+": ("+self.suite.name+","+self.test.name+")"

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('suite', 'test'), ('suite', 'order'))

class TestMappingEvents(Events):
    model = TestMapping
    on_insert = on_update = ['suite', 'test']
    on_delete = []

