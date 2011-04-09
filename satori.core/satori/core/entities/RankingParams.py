# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

class RankingParams(Entity):
    """Model. Intermediary for many-to-many relationship between Rankings and
    ProblemMappings.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_rankingparams')

    ranking       = models.ForeignKey('Ranking', related_name='ranking_params', on_delete=models.CASCADE)
    problem       = models.ForeignKey('ProblemMapping', related_name='ranking_params+', on_delete=models.CASCADE)
    test_suite    = models.ForeignKey('TestSuite', related_name='ranking_params+', null=True, on_delete=models.PROTECT)

    params        = AttributeGroupField(PCArg('self', 'MANAGE'), PCDeny(), '')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('ranking', 'problem'),)

    def save(self, *args, **kwargs):
        self.fixup_params()
        super(RankingParams, self).save(*args, **kwargs)

    @classmethod
    def inherit_rights(cls):
        inherits = super(RankingParams, cls).inherit_rights()
        cls._inherit_add(inherits, 'MANAGE', 'ranking', 'MANAGE')
        return inherits

class RankingParamsEvents(Events):
    model = RankingParams
    on_insert = on_update = ['ranking', 'problem', 'test_suite']
    on_delete = []
