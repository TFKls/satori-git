# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class RankingParams(Entity):
    """Model. Intermediary for many-to-many relationship between Rankings and
    ProblemMappings.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_rankingparams')

    ranking       = models.ForeignKey('Ranking', related_name='ranking_params')
    problem       = models.ForeignKey('ProblemMapping', related_name='ranking_params+')
    test_suite    = models.ForeignKey('TestSuite', related_name='ranking_params+', null=True)

    params        = AttributeGroupField(PCArg('self', 'MANAGE'), PCDeny(), '')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('ranking', 'problem'),)

    class ExportMeta(object):
        fields = [('ranking', 'VIEW'), ('problem', 'VIEW'), ('test_suite', 'VIEW')]

    def save(self, *args, **kwargs):
        self.fixup_params()
        super(RankingParams, self).save(*args, **kwargs)

    @classmethod
    def inherit_rights(cls):
        inherits = super(RankingParams, cls).inherit_rights()
        cls._inherit_add(inherits, 'MANAGE', 'ranking', 'MANAGE')
        return inherits

    @ExportMethod(DjangoStruct('RankingParams'), [DjangoStruct('RankingParams'), TypedMap(unicode, AnonymousAttribute)], PCArgField('fields', 'ranking', 'MANAGE'), [CannotSetField])
    @staticmethod
    def create(fields, params):
        rparams = RankingParams()
        rparams.forbid_fields(fields, ['id'])
        rparams.update_fields(fields, ['ranking', 'problem', 'test_suite'])
        if rparams.ranking.contest != rparams.problem.contest or rparams.problem.problem != rparams.test_suite.problem:
            raise CannotSetField()
        rparams.save()
        rparams.params_set_map(params)
        rparams.ranking.rejudge()
        return params

    @ExportMethod(DjangoStruct('RankingParams'), [DjangoId('RankingParams'), DjangoStruct('RankingParams'), TypedMap(unicode, AnonymousAttribute)], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields, params):
        self.forbid_fields(fields, ['id', 'ranking', 'problem'])
        self.update_fields(fields, ['test_suite'])
        if self.ranking.contest != self.problem.contest or self.problem.problem != self.test_suite.problem:
            raise CannotSetField()
        self.save()
        self.params_set_map(params)
        self.ranking.rejudge()
        return self

class RankingParamsEvents(Events):
    model = RankingParams
    on_insert = on_update = ['ranking', 'problem', 'test_suite']
    on_delete = []
