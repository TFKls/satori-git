# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models

from satori.core.export        import ExportMethod
from satori.core.export_django import ExportModel, generate_attribute_group
from satori.core.dbev               import Events

from satori.core.models import Entity

@ExportModel
class ProblemResult(Entity):
    """Model. Cumulative result of all submits of a particular ProblemMapping by
    a single Contestant.
    """

    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_problemresult')

    contestant  = models.ForeignKey('Contestant')
    problem     = models.ForeignKey('ProblemMapping')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contestant', 'problem'),)

    class ExportMeta(object):
        fields = [('contestant', 'VIEW'), ('problem', 'VIEW')]

class ProblemResultEvents(Events):
    model = ProblemResult
    on_insert = on_update = ['contestant', 'problem']
    on_delete = []

