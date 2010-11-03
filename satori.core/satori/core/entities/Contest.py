# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models

from satori.core.export        import ExportMethod, PCOr, PCGlobal, PCTokenUser, PCArg, token_container, Struct, TypedList
from satori.core.export_django import ExportModel, DjangoId, DjangoStruct, DjangoIdList, generate_attribute_group
from satori.core.dbev               import Events

from satori.core.models import Entity, Submit



@ExportModel
class Contest(Entity):
    """Model. Description of a contest.
    """
    
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_contest')

    name        = models.CharField(max_length=50, unique=True)
    problems    = models.ManyToManyField('Problem', through='ProblemMapping')
    contestant_role = models.ForeignKey('Role')

    generate_attribute_group('Contest', 'files', 'VIEW', 'EDIT', globals(), locals())

    class ExportMeta(object):
        fields = [('name', 'VIEW'), ('contestant_role', 'VIEW')]

    def save(self):
        self.fixup_files()
        super(Contest, self).save()

    def __str__(self):
        return self.name
    # TODO: add presentation options

    @classmethod
    def inherit_rights(cls):
        inherits = super(Contest, cls).inherit_rights()
        cls._inherit_add(inherits, 'OBSERVE', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'VIEWTASKS', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'APPLY', 'id', 'JOIN')
        cls._inherit_add(inherits, 'JOIN', 'id', 'MANAGE')
        return inherits

    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contest'), DjangoId('User')], PCOr(PCTokenUser('user'), PCArg('self', 'MANAGE')))
    def find_contestant(self, user):
        try:
            return Contestant.objects.get(contest=self, children__id=user.id)
        except Contestant.DoesNotExist:
            return None

    # TODO: check if exists
    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contest'), DjangoIdList('User')], PCArg('self', 'MANAGE'))
    def create_contestant(self, user_list):
        c = Contestant()
        c.accepted = True
        c.contest = self
        c.save()
        self.contestant_role.add_member(c)
        Privilege.grant(c, c, 'OBSERVE')
        for user in user_list:
            c.add_member(user)

    @ExportMethod(DjangoStruct('Contest'), [unicode], PCGlobal('MANAGE_CONTESTS'))
    @staticmethod
    def create_contest(name):
        c = Contest()
        c.name = name
        r = Role(name=name+'_contestant', )
        r.save()
        c.contestant_role = r
        c.save()
        Privilege.grant(token_container.token.user, c, 'MANAGE')
        Privilege.grant(r, c, 'VIEW')
        return c

    # TODO: check if exists
    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contest')], PCArg('self', 'APPLY'))
    def join_contest(self):
        c = Contestant()
        c.contest = self
        c.accepted = bool(Privilege.demand(self, 'JOIN'))
        c.save()
        if c.accepted:
            self.contestant_role.add_member(c)
        c.add_member(token_container.token.user)
        return c

    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contest'), DjangoId('Contestant')], PCArg('self', 'MANAGE'))
    def accept_contestant(self, contestant):
        if contestant.contest != self:
            raise "Go away"
        contestant.accepted = True
        contestant.save()
        self.contestant_role.add_member(contestant)
        return contestant

    @ExportMethod(DjangoStruct('Submit'), [DjangoId('Contest'), DjangoId('ProblemMapping'), unicode, unicode], PCArg('problem_mapping', 'SUBMIT'))
    def submit(self, problem_mapping, content, filename):
        contestant = self.find_contestant(token_container.token.user)
        if problem_mapping.contest != self:
            raise "Go away"
        submit = Submit()
        submit.contestant = contestant
        submit.problem = problem_mapping
        submit.save()
        Privilege.grant(contestant, submit, 'VIEW')
        blob = submit.oa_set_blob('content', filename=filename)
        blob.write(content)
        blob.close()
        TestSuiteResult(submit=submit, test_suite=problem_mapping.default_test_suite).save()
        return submit

    ResultToRender = Struct('ResultToRender', (
        ('submit', DjangoId('Submit'), True),
        ('problem', unicode, True),
        ('contestant', unicode, True),
        ('status', unicode, True),
        ('details', unicode, True),
    ))
    @staticmethod
    def submit_to_result_to_render(submit):
        return {
        	'submit' : submit,
            'problem' : submit.problem.code,
            'contestant' : submit.contestant.name_auto(),
            'status' : submit.get_test_suite_status(),
            'details' : submit.get_test_suite_report()
            }

    @ExportMethod(TypedList(ResultToRender), [DjangoId('Contest'), DjangoId('ProblemMapping'), int, int], PCArg('self', 'OBSERVE'))
    def get_all_results(self, problem=None, limit=20, offset=0):
        res = []
        q = Submit.objects.filter(contestant__contest=self)
        if problem:
        	q = q.filter(problem=problem)
        for submit in q.order_by('-id')[offset:offset+limit]:
        	res.append(Contest.submit_to_result_to_render(submit))
        return res

    @ExportMethod(TypedList(ResultToRender), [DjangoId('Contest'), DjangoId('Contestant'), DjangoId('ProblemMapping'), int, int], PCArg('contestant', 'OBSERVE'))
    def get_results(self, contestant, problem=None, limit=20, offset=0):
        res = []
        q = Submit.objects.filter(contestant=contestant)
        if problem:
        	q = q.filter(problem=problem)
        for submit in q.order_by('-id')[offset:offset+limit]:
        	res.append(Contest.submit_to_result_to_render(submit))
        return res


class ContestEvents(Events):
    model = Contest
    on_insert = on_update = ['name']
    on_delete = []

