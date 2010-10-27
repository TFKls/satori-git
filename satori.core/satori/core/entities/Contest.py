# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models

from satori.core.export        import ExportMethod, PCOr, PCGlobal, PCTokenUser, PCArg, token_container
from satori.core.export_django import ExportModel, DjangoId, DjangoStruct, DjangoIdList, generate_attribute_group
from satori.dbev               import Events

from satori.core.models import Entity

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

    def inherit_right(self, right):
        right = str(right)
        ret = super(Contest, self).inherit_right(right)
        if right == 'VIEW' or right == 'OBSERVE' or right == 'VIEWTASKS':
            ret.append((self,'MANAGE'))
        if right == 'APPLY':
            ret.append((self,'JOIN'))
        return ret

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
        blob = OpenAttribute.create_blob()
        blob.write(content)
        hash = blob.close()
        submit.data_set_blob_hash(name='content', hash=hash, filename=filename)
        TestSuiteResult(submit=submit, test_suite=problem_mapping.default_test_suite).save()
        return submit


class ContestEvents(Events):
    model = Contest
    on_insert = on_update = ['name']
    on_delete = []

