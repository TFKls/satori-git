from django.db import models
from satori.dbev import events
from satori.ars import django_
from satori.core.models._Object import Object

class ProblemMapping(Object):
    """Model. Intermediary for many-to-many relationship between Contests and
    ProblemIncarnations.
    """
    __module__ = "satori.core.models"

    contest     = models.ForeignKey('Contest')
    problem     = models.ForeignKey('Problem')
    code        = models.CharField(max_length=10)
    title       = models.CharField(max_length=64)
    
    def __unicode__(self):
        return self.code+": "+self.title+ " ("+self.contest.name+","+self.problem.name+")"

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'code'), ('contest', 'problem'))

class ProblemMappingEvents(events.Events):
    model = ProblemMapping
    on_insert = on_update = ['contest', 'problem']
    on_delete = []

class ProblemMappingOpers(django_.Opers):
    problemmapping = django_.ModelProceduresProvider(ProblemMapping)

