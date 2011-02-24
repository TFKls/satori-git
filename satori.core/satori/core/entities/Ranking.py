# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class Ranking(Entity):
    """Model. Ranking in a Contest.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_ranking')

    contest       = models.ForeignKey('Contest', related_name='rankings')
    name          = models.CharField(max_length=50)
    aggregator    = models.CharField(max_length=128)
    header        = models.TextField()
    footer        = models.TextField()
    is_public     = models.BooleanField()
    problems      = models.ManyToManyField('ProblemMapping', related_name='rankings+', through='RankingParams')

    params         = AttributeGroupField(PCArg('self', 'MANAGE'), PCDeny(), '')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'name'),)

    class ExportMeta(object):
        fields = [('contest', 'VIEW'), ('name', 'VIEW'), ('aggregator', 'MANAGE'), ('header', 'MANAGE'), ('footer', 'MANAGE'), ('is_public', 'MANAGE')]

    @classmethod
    def inherit_rights(cls):
        inherits = super(Ranking, cls).inherit_rights()
        cls._inherit_add(inherits, 'VIEW', 'contest', 'VIEW', 'is_public', '1')
        cls._inherit_add(inherits, 'MANAGE', 'contest', 'MANAGE')
        return inherits

    def save(self, *args, **kwargs):
        self.fixup_params()
        from satori.core.checking.aggregators import aggregators
        if not self.aggregator in aggregators:
            raise ValueError('Aggregator '+self.aggregator+' is not allowed')
        super(Ranking,self).save(*args,**kwargs)

    
    @ExportMethod(DjangoStruct('Ranking'), [DjangoStruct('Ranking'), TypedMap(unicode, AnonymousAttribute),
        TypedMap(DjangoId('ProblemMapping'), DjangoId('TestSuite')), TypedMap(DjangoId('ProblemMapping'), TypedMap(unicode, AnonymousAttribute))], 
        PCAnd(PCArgField('fields', 'contest', 'MANAGE'), PCEachValue('params', PCRawBlob('item')), PCEachValue('problem_test_suite_params', PCEachValue('item', PCRawBlob('item')))),
        [CannotSetField])
    @staticmethod
    def create(fields, params, problem_test_suites, problem_test_suite_params):
        ranking = Ranking()
        ranking.forbid_fields(fields, ['id', 'header', 'footer'])
        ranking.update_fields(fields, ['contest', 'name', 'aggregator', 'is_public'])
        ranking.save()
        ranking.params_set_map(params)
        for problem in ranking.contest.problem_mappings.all():
            ranking_params = RankingParams.get_or_create(ranking=ranking, problem=problem)
            if problem in problem_test_suites:
                if problem_test_suites[problem].problem != problem.problem:
                    raise RuntimeError('Invalid test suite')
                ranking_params.test_suite = problem_test_suites[problem]
            ranking_params.save()
            if problem in problem_test_suite_params:
                ranking_params.params_set_map(problem_test_suite_params[problem])
            else:
                ranking_params.params_set_map({})
        ranking.rejudge()
        return ranking

    @ExportMethod(DjangoStruct('Ranking'), [DjangoId('Ranking'), DjangoStruct('Ranking')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, ['id', 'header', 'footer', 'contest, aggregator'])
        self.update_fields(fields, ['name', 'is_public'])
        self.save()
        return self

    @ExportMethod(DjangoStruct('Ranking'), [DjangoId('Ranking'), DjangoStruct('Ranking'), TypedMap(unicode, AnonymousAttribute),
        TypedMap(DjangoId('ProblemMapping'), DjangoId('TestSuite')), TypedMap(DjangoId('ProblemMapping'), TypedMap(unicode, AnonymousAttribute))], 
        PCAnd(PCArg('self', 'MANAGE'), PCEachValue('params', PCRawBlob('item')), PCEachValue('problem_params', PCEachValue('item', PCRawBlob('item')))),
        [CannotSetField])
    def modify_full(self, fields, params, problem_test_suites, problem_params):
        self.forbid_fields(fields, ['id', 'header', 'footer', 'contest'])
        modified = self.update_fields(fields, ['name', 'aggregator', 'is_public'])
        self.save()
        self.params_set_map(params)
        for problem in self.contest.problem_mappings.all():
            ranking_params = RankingParams.get_or_create(ranking=self, problem=problem)
            if problem in problem_test_suites:
                if problem_test_suites[problem].problem != problem.problem:
                    raise RuntimeError('Invalid test suite')
                ranking_params.test_suite = problem_test_suites[problem]
            ranking_params.save()
            if problem in problem_params:
                ranking_params.params_set_map(problem_params[problem])
            else:
                ranking_params.params_set_map({})
        self.rejudge()
        return self

    @ExportMethod(TypedMap(DjangoStruct('ProblemMapping'), DjangoStruct('TestSuite')), [DjangoId('Ranking')], PCArg('self', 'MANAGE'))
    def get_problem_test_suites(self):
        ret = {}
        for param in self.ranking_params.all():
            if param.test_suite is not None:
                ret[param.poblem] = param.test_suite
        return ret

    @ExportMethod(TypedMap(DjangoStruct('ProblemMapping'), TypedMap(DjangoId('ProblemMapping'), TypedMap(unicode, AnonymousAttribute))), [DjangoId('Ranking')], PCArg('self', 'MANAGE'))
    def get_problem_params(self):
        ret = {}
        for param in self.ranking_params.all():
            ret[param.poblem] = param.params_get_map()
        return ret

    @ExportMethod(NoneType, [DjangoId('Ranking')], PCArg('self', 'MANAGE'))
    def rejudge(self):
        RawEvent().send(Event(type='checking_rejudge_ranking', id=self.id))

    @ExportMethod(unicode, [DjangoId('Ranking')], PCArg('self', 'VIEW'))
    def full_ranking(self):
        res = self.header
        res += ''.join([ entry.row for entry in self.entries.all() ])
        res += self.footer
        return res

class RankingEvents(Events):
    model = Ranking
    on_insert = on_update = ['contest', 'name']
