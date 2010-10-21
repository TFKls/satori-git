# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models
from satori.dbev import Events
from satori.core.models import Entity

class ProblemResult(Entity):
    """Model. Cumulative result of all submits of a particular ProblemMapping by
    a single Contestant.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Entity, parent_link=True, related_name='cast_problemresult')

    contestant  = models.ForeignKey('Contestant')
    problem     = models.ForeignKey('ProblemMapping')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contestant', 'problem'),)

class ProblemResultEvents(Events):
    model = ProblemResult
    on_insert = on_update = ['contestant', 'problem']
    on_delete = []

#! module api

from satori.ars.wrapper import WrapperClass
from satori.core.cwrapper import ModelWrapper
from satori.core.models import ProblemResult

class ApiProblemResult(WrapperClass):
    problem_result = ModelWrapper(ProblemResult)

