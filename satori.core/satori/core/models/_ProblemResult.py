from django.db import models
from satori.dbev import events
from satori.ars import django_
from satori.core.models._Object import Object

class ProblemResult(Object):
    """Model. Cumulative result of all submits of a particular ProblemIncarnation by
    a single Contestant.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_problemresult')

    contestant  = models.ForeignKey('Contestant')
    problem     = models.ForeignKey('ProblemIncarnation')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contestant', 'problem'),)

class ProblemResultEvents(events.Events):
    model = ProblemResult
    on_insert = on_update = ['contestant', 'problem']
    on_delete = []

class ProblemResultOpers(django_.Opers):
    problemresult = django_.ModelProceduresProvider(ProblemResult)

