from django.db import models
from satori.dbev import events
from satori.ars import wrapper
from satori.core import cwrapper
from satori.core.models._Object import Object
from satori.core.models.modules import AGGREGATORS1
from satori.core.models.modules import DISPATCHERS

class TestSuite(Object):
    """Model. A group of tests, with dispatch and aggregation algorithm.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_testsuite')

    owner       = models.ForeignKey('User', null=True)
    problem     = models.ForeignKey('Problem', null=True)
    name        = models.CharField(max_length=50)
    tests       = models.ManyToManyField('Test', through='TestMapping')
    dispatcher  = models.CharField(max_length=128, choices=DISPATCHERS)
    aggregator1 = models.CharField(max_length=128, choices=AGGREGATORS1)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('problem', 'name'),)

class TestSuiteEvents(events.Events):
    model = TestSuite
    on_insert = on_update = ['owner', 'problem', 'name']
    on_delete = []

class TestSuiteWrapper(wrapper.WrapperClass):
    testsuite = cwrapper.ModelWrapper(TestSuite)

