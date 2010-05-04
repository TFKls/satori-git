from django.db import models
from satori.dbev import events
from satori.ars import django2ars
from satori.core.models._Object import Object
from satori.core.models.modules import AGGREGATORS3

class Contest(Object):
    """Model. Description of a contest.
    """
    __module__ = "satori.core.models"

    name        = models.CharField(max_length=50, unique=True)
    problems    = models.ManyToManyField('ProblemIncarnation', through='ProblemMapping')
    aggregator3 = models.CharField(max_length=128, choices=AGGREGATORS3)
    # TODO: add presentation options
    
class ContestEvents(events.Events):
    model = Contest
    on_insert = on_update = ['name']
    on_delete = []

class ContestOpers(django2ars.Opers):
    contest = django2ars.ModelOpers(Contest)

