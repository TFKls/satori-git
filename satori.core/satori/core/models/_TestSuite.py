# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._Object import Object
from satori.core.models.modules import DISPATCHERS

class TestSuite(Object):
    """Model. A group of tests, with dispatch and aggregation algorithm.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_testsuite')

    owner       = models.ForeignKey('User')
    problem     = models.ForeignKey('Problem')
    name        = models.CharField(max_length=50)
    description = models.TextField(blank=True, default="")
    tests       = models.ManyToManyField('Test', through='TestMapping')
    dispatcher  = models.CharField(max_length=128, choices=DISPATCHERS)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('problem', 'name'),)

class TestSuiteEvents(events.Events):
    model = TestSuite
    on_insert = on_update = ['owner', 'problem', 'name']
    on_delete = []

