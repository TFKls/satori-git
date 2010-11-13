# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev               import Events

from satori.core.models import Entity

@ExportModel
class ContestRanking(Entity):
    """Model. Ranking in a Contest.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_contestranking')

    contest     = models.ForeignKey('Contest')
    name        = models.CharField(max_length=50)
    aggregator  = models.CharField(max_length=128)
    pending     = models.BooleanField(default=True)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'name'),)



class ContestRankingEvents(Events):
    model = ContestRanking
    on_insert = on_update = ['contest', 'name']
