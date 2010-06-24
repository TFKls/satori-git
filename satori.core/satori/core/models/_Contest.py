from django.db import models
from satori.dbev import events
from satori.ars import django_
from satori.core.models._Object import Object
from satori.core.models.modules import AGGREGATORS3

class Contest(Object):
    """Model. Description of a contest.
    """
    __module__ = "satori.core.models"
    
    joiningChoices = [ ('Private', 'Private'),('Moderated','Moderated'),('Public','Public') ]
    name        = models.CharField(max_length=50, unique=True)
    problems    = models.ManyToManyField('Problem', through='ProblemMapping')
    joining     = models.CharField(max_length=30, choices=joiningChoices)
    aggregator3 = models.CharField(max_length=128, choices=AGGREGATORS3)
    def __unicode__(self):
        return self.name
    # TODO: add presentation options

    
class ContestEvents(events.Events):
    model = Contest
    on_insert = on_update = ['name']
    on_delete = []

class ContestOpers(django_.Opers):
    contest = django_.ModelProceduresProvider(Contest)

