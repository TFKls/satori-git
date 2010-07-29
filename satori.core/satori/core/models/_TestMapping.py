from django.db import models
from satori.dbev import events
from satori.ars import wrapper
from satori.core import cwrapper
from satori.core.models._Object import Object

class TestMapping(Object):
    """Model. Intermediary for many-to-many relationship between TestSuites and
    Tests.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_testmapping')

    suite       = models.ForeignKey('TestSuite')
    test        = models.ForeignKey('Test')
    code        = models.CharField(max_length=10)
    title       = models.CharField(max_length=64)
    
    def __unicode__(self):
        return self.code+": "+self.title+ " ("+self.suite.name+","+self.test.name+")"

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('suite', 'code'), ('suite', 'test'))

class TestMappingEvents(events.Events):
    model = TestMapping
    on_insert = on_update = ['suite', 'test']
    on_delete = []

class TestMappingWrapper(wrapper.WrapperClass):
    testmapping = cwrapper.ModelWrapper(TestMapping)

