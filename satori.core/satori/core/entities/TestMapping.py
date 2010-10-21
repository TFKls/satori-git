# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models
from satori.dbev import Events
from satori.core.models import Entity

class TestMapping(Entity):
    """Model. Intermediary for many-to-many relationship between TestSuites and
    Tests.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Entity, parent_link=True, related_name='cast_testmapping')

    suite       = models.ForeignKey('TestSuite')
    test        = models.ForeignKey('Test')
    order       = models.IntegerField()

    def __str__(self):
        return str(self.order)+": ("+self.suite.name+","+self.test.name+")"

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('suite', 'test'), ('suite', 'order'))
        ordering = ('order',)

class TestMappingEvents(Events):
    model = TestMapping
    on_insert = on_update = ['suite', 'test']
    on_delete = []

#! module api

from satori.ars.wrapper import WrapperClass
from satori.core.cwrapper import ModelWrapper
from satori.core.models import TestMapping

class ApiTestMapping(WrapperClass):
    test_mapping = ModelWrapper(TestMapping)

