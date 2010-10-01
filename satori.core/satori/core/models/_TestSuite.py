# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import Events
from satori.core.models._Entity import Entity
from datetime import datetime

class TestSuite(Entity):
    """Model. A group of tests, with dispatch and aggregation algorithm.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Entity, parent_link=True, related_name='cast_testsuite')

    problem      = models.ForeignKey('Problem')
    name         = models.CharField(max_length=50)
    description  = models.TextField(blank=True, default="")
    tests        = models.ManyToManyField('Test', through='TestMapping')
    dispatcher   = models.CharField(max_length=128)
    accumulators = models.CharField(max_length=1024)

    def inherit_right(self, right):
        right = str(right)
        ret = super(TestSuite, self).inherit_right(right)
        if right=='EDIT':
            ret.append((self.problem,'EDIT'))
        return ret

    def save(self, *args, **kwargs):
        from satori.core.checking.dispatchers import dispatchers
        from satori.core.checking.accumulators import accumulators
        if not self.name:
            self.name = str(datetime.now())
        if not self.dispatcher in dispatchers:
            raise ValueError('Dispatcher '+self.dispatcher+' is not allowed')
        for accumulator in self.accumulators.split(','):
            if not accumulator in accumulators:
                raise ValueError('Accumulator '+accumulator+' is not allowed')
        super(TestSuite,self).save(*args,**kwargs)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('problem', 'name'),)

class TestSuiteEvents(Events):
    model = TestSuite
    on_insert = on_update = ['owner', 'problem', 'name']
    on_delete = []

