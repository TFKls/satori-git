# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models

from satori.core.export        import ExportMethod
from satori.core.export_django import ExportModel
from satori.dbev               import Events

from satori.core.models import Entity

@ExportModel
class ContestRanking(Entity):
    """Model. Ranking in a Contest.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Entity, parent_link=True, related_name='cast_contestranking')

    contest     = models.ForeignKey('Contest')
    name        = models.CharField(max_length=50)
    aggregator  = models.CharField(max_length=128)
    pending     = models.BooleanField(default=True)

    def inherit_right(self, right):
        right = str(right)
        ret = super(ContestRanking, self).inherit_right(right)
        if right == 'VIEW':
            ret.append((self.contest,'MANAGE'))
        return ret

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'name'),)



class ContestRankingEvents(Events):
    model = ContestRanking
    on_insert = on_update = ['contest', 'name']
