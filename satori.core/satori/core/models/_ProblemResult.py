from django.db import models
from satori.dbev import events
from satori.ars import wrapper
from satori.core import cwrapper
from satori.core.models._Object import Object

class ProblemResult(Object):
    """Model. Cumulative result of all submits of a particular ProblemMapping by
    a single Contestant.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_problemresult')

    contestant  = models.ForeignKey('Contestant')
    problem     = models.ForeignKey('ProblemMapping')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contestant', 'problem'),)

class ProblemResultEvents(events.Events):
    model = ProblemResult
    on_insert = on_update = ['contestant', 'problem']
    on_delete = []

class ProblemResultWrapper(wrapper.WrapperClass):
    problemresult = cwrapper.ModelWrapper(ProblemResult)

