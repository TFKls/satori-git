# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._Object import Object
from satori.core.models.modules import DISPATCHERS
from datetime import datetime

class TestSuite(Object):
    """Model. A group of tests, with dispatch and aggregation algorithm.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_testsuite')

    problem     = models.ForeignKey('Problem')
    name        = models.CharField(max_length=50)
    description = models.TextField(blank=True, default="")
    tests       = models.ManyToManyField('Test', through='TestMapping')
    dispatcher  = models.CharField(max_length=128, choices=DISPATCHERS)
    
    def inherit_right(self, right):
        right = str(right)
        ret = super(TestSuite, self).inherit_right(right)
        if right=='EDIT':
            ret.append((self.problem,'EDIT'))
        return ret

    def save(self, *args, **kwargs):
        if self.name == None:
            self.name = str(datetime.now())
        super(TestSuite,self).save(*args,**kwargs)
        
    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('problem', 'name'),)

class TestSuiteEvents(events.Events):
    model = TestSuite
    on_insert = on_update = ['owner', 'problem', 'name']
    on_delete = []

