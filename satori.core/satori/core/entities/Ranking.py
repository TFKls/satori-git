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
    name          = models.CharField(max_length=64)
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
        cls._inherit_add(inherits, 'VIEW', 'id', 'VIEW_FULL')
        cls._inherit_add(inherits, 'VIEW_FULL', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'VIEW_FULL', 'contest', 'VIEW', 'is_public', '1')
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
        PCAnd(PCArgField('fields', 'contest', 'MANAGE'), PCEachValue('params', PCRawBlob('item')), PCEachValue('problem_params', PCEachValue('item', PCRawBlob('item')))),
        [CannotSetField])
    @staticmethod
    def create(fields, params, problem_test_suites, problem_params):
        ranking = Ranking()
        ranking.forbid_fields(fields, ['id', 'header', 'footer'])
        ranking.update_fields(fields, ['contest', 'name', 'aggregator', 'is_public'])
        ranking.save()
        ranking.params_set_map(params)
        set_params = {}
        for problem,suite in problem_test_suites.items():
            if problem.contest != ranking.contest:
                raise CannotSetField
            if suite.problem != problem.problem:
                raise CannotSetField
            ranking_params = RankingParams(ranking=ranking, problem=problem, test_suite=suite)
            ranking_params.save()
            set_params[problem.id] = ranking_params
        for problem,oa_map in problem_params.items():
            if problem.contest != ranking.contest:
                raise CannotSetField
            if problem.id in set_params:
                ranking_params = set_params[problem.id]
            else:
                ranking_params = RankingParams(ranking=ranking, problem=problem)
                ranking_params.save()
            ranking_params.params_set_map(oa_map)
            set_params[problem.id] = ranking_params
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
        set_params = {}
        for problem,suite in problem_test_suites.items():
            if problem.contest != self.contest:
                raise CannotSetField
            if suite.problem != problem.problem:
                raise CannotSetField
            ranking_params = RankingParams.objects().get_or_create(ranking=self, problem=problem)[0]
            ranking_params.test_suite=suite
            ranking_params.save()
            ranking_params.params_set_map({})
            set_params[problem.id] = ranking_params
        for problem,oa_map in problem_params.items():
            if problem.contest != self.contest:
                raise CannotSetField
            if problem.id in set_params:
                ranking_params = set_params[problem.id]
            else:
                ranking_params = RankingParams.objects().get_or_create(ranking=self, problem=problem)[0]
                ranking_params.save()
            ranking_params.params_set_map(oa_map)
            set_params[problem.id] = ranking_params
        for ex_params in self.ranking_params.objects().all():
            if ex_params.id not in set_params:
                ex_params.delete()
        self.rejudge()
        return self

    @ExportMethod(TypedMap(DjangoStruct('ProblemMapping'), DjangoStruct('TestSuite')), [DjangoId('Ranking')], PCArg('self', 'MANAGE'))
    def get_problem_test_suites(self):
        ret = {}
        for param in self.ranking_params.all():
            if param.test_suite is not None:
                ret[param.poblem] = param.test_suite
        return ret

    @ExportMethod(NoneType, [DjangoId('Ranking'), TypedMap(DjangoId('ProblemMapping'), DjangoId('TestSuite'))], PCArg('self', 'MANAGE'))
    def set_problem_test_suites(self, problem_test_suites):
        for problem, suite in problem_test_suites.items():
            if problem.contest != self.contest:
                raise CannotSetField
            if suite.problem != problem.problem:
                raise CannotSetField
            param = RankingParams.objects.get_or_create(ranking=self, problem=problem)[0]
            param.test_suite = suite
            param.save()

    @ExportMethod(TypedMap(DjangoStruct('ProblemMapping'), TypedMap(unicode, AnonymousAttribute)), [DjangoId('Ranking')], PCArg('self', 'MANAGE'))
    def get_problem_params(self):
        ret = {}
        for param in self.ranking_params.all():
            ret[param.poblem] = param.params_get_map()
        return ret

    @ExportMethod(NoneType, [DjangoId('Ranking', TypedMap(DjangoId('ProblemMapping'), TypedMap(unicode, AnonymousAttribute)))], PCAnd(PCArg('self', 'MANAGE'), PCEachValue('problem_params', PCEachValue('item', PCRawBlob('item')))))
    def set_problem_params(self, problem_params):
        for problem, oa_map in problem_params.items():
            if problem.contest != self.contest:
                raise CannotSetField
            param = RankingParams.objects.get_or_create(ranking=self, problem=problem)[0]
            param.save()
            param.params_set_map(oa_map)

    @ExportMethod(NoneType, [DjangoId('Ranking')], PCArg('self', 'MANAGE'))
    def rejudge(self):
        RawEvent().send(Event(type='checking_rejudge_ranking', id=self.id))

    @ExportMethod(unicode, [DjangoId('Ranking')], PCArg('self', 'VIEW_FULL'))
    def full_ranking(self):
        res = self.header
        res += ''.join([ entry.row for entry in self.entries.all() ])
        res += self.footer
        return res

class RankingEvents(Events):
    model = Ranking
    on_insert = on_update = ['contest', 'name']
