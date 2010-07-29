from django.db import models
from satori.dbev import events
from satori.ars import wrapper
from satori.core import cwrapper
from satori.core.models._Object import Object
from satori.core.models.modules import AGGREGATORS2

class ProblemIncarnation(Object):
    """Model. Specific version of a Problems, as used in (one or more) Contests.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_problemincarnation')

    problem     = models.ForeignKey('Problem')
    description = models.TextField()
    test_suite  = models.ForeignKey('TestSuite')
    aggregator2 = models.CharField(max_length=128, choices=AGGREGATORS2)

class ProblemIncarnationEvents(events.Events):
    model = ProblemIncarnation
    on_insert = on_update = ['problem', 'test_suite']
    on_delete = []

class ProblemIncarnationWrapper(wrapper.WrapperClass):
    problemincarnation = cwrapper.ModelWrapper(ProblemIncarnation)


