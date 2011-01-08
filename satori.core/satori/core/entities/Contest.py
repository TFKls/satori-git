# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.ars.server import server_info
from satori.core.dbev  import Events

from satori.core.models import Entity

ResultToRender = Struct('ResultToRender', (
    ('submit', DjangoStruct('Submit'), True),
    ('problem', unicode, True),
    ('contestant', unicode, True),
    ('status', unicode, True),
    ('details', unicode, True),
))
ResultsToRender = Struct('ResultsToRender', (
    ('count', int, True),
    ('results', TypedList(ResultToRender), True),
))
ContestantToRender = Struct('ContestantToRender', (
    ('contestant', DjangoStruct('Contestant'), True),
    ('name', unicode, True),
    ('members', TypedList(DjangoStruct('User')), True),
    ('admin', bool, True),
))
ContestantsToRender = Struct('ContestantsToRender', (
    ('count', int, True),
    ('contestants', TypedList(ContestantToRender), True),
))
AlreadyRegistered = DefineException('AlreadyRegisteres', 'The specified user \'{login}\' is already registered',
    [('login', unicode, False)])

@ExportModel
class Contest(Entity):
    """Model. Description of a contest.

    rights:
        VIEW_INTRA_FILES
        VIEW_TASKS
        APPLY
        JOIN
        OBSERVE
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_contest')

    name            = models.CharField(max_length=50, unique=True)
    problems        = models.ManyToManyField('Problem', through='ProblemMapping', related_name='contests')
    contestant_role = models.ForeignKey('Role', related_name='contests+')
    archived        = models.BooleanField(default=False)

    lock_start   = models.DateTimeField(null=True)
    lock_finish  = models.DateTimeField(null=True)
    lock_address = models.IPAddressField(default='0.0.0.0')
    lock_netmask = models.IPAddressField(default='255.255.255.255')

    public_files = AttributeGroupField(PCArg('self', 'VIEW'), PCArg('self', 'MANAGE'), '')
    intra_files  = AttributeGroupField(PCArg('self', 'VIEW_INTRA_FILES'), PCArg('self', 'MANAGE'), '')

    class ExportMeta(object):
        fields = [('name', 'VIEW'), ('contestant_role', 'MANAGE'), ('lock_start', 'MANAGE'), ('lock_finish', 'MANAGE'), ('lock_address', 'MANAGE'), ('lock_netmask', 'MANAGE')]

    @classmethod
    def inherit_rights(cls):
        inherits = super(Contest, cls).inherit_rights()
        cls._inherit_add(inherits, 'APPLY', 'id', 'JOIN')
        cls._inherit_add(inherits, 'JOIN', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'SUBMIT', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'OBSERVE', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'VIEW_TASKS', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'ASK_QUESTIONS', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'VIEW_INTRA_FILES', 'id', 'MANAGE')
        return inherits

    def save(self, *args, **kwargs):
        self.fixup_public_files()
        self.fixup_intra_files()
        super(Contest, self).save(*args, **kwargs)

    def __str__(self):
        return self.name
    # TODO: add presentation options

    @ExportMethod(DjangoStruct('Contest'), [], PCPermit())
    @staticmethod
    def get_current_lock():
        contests = Contest.objects.filter(lock_start__lte=datetime.now(), lock_finish__gte=datetime.now())
        contests = [contest for contest in contests
            if (ipaddr.IPv4Address(server_info.client_ip) in ipaddr.IPv4Network(contest.lock_address + '/' + contest.lock_netmask))
        ]
        
        if len(contests) == 0:
            return None
        if len(contests) > 1:
            raise Contest.MultipleObjectsReturned()
        else:
            return contests[0]
        
    @ExportMethod(DjangoStruct('Contest'), [DjangoStruct('Contest')], PCGlobal('MANAGE_CONTESTS'), [CannotSetField])
    @staticmethod
    def create(fields):
        contest = Contest()
        contest.forbid_fields(fields, ['id', 'contestant_role'])
        contest.update_fields(fields, ['name', 'archived', 'lock_start', 'lock_finish', 'lock_address', 'lock_netmask'])
        contestant_role = Role(name='Contestant of ' + contest.name)
        contestant_role.save()
        contest.contestant_role = contestant_role
        contest.save()
        Privilege.grant(token_container.token.role, contest, 'MANAGE')
        Privilege.grant(contest.contestant_role, contest, 'VIEW')
        return contest
   
    @ExportMethod(DjangoStruct('Contest'), [DjangoId('Contest'), DjangoStruct('Contest')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields):
        contest.forbid_fields(fields, ['id', 'contestant_role'])
        modified = contest.update_fields(fields, ['name', 'archived', 'lock_start', 'lock_finish', 'lock_address', 'lock_netmask'])
        if 'name' in modified:
            role = contest.contestant_role
            role.name='Contestant of ' + contest.name
            role.save()
        return self

    @ExportMethod(NoneType, [DjangoId('Contest')], PCArg('self', 'MANAGE'))
    def disable_lock(self):
        self.lock_start = None
        self.lock_finish = None
        self.lock_address = '0.0.0.0'
        self.lock_netmask = '255.255.255.255'
        self.save()

    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contest'), DjangoId('Role')], PCOr(PCTokenUser('user'), PCArg('self', 'MANAGE')))
    def find_contestant(self, user):
        try:
            return Contestant.objects.get(contest=self, children__id=user.id)
        except Contestant.DoesNotExist:
            try:
                return Contestant.objects.get(contest=self, id=user.id)
            except Contestant.DoesNotExist:
               return None

    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contest')], PCAnd(PCTokenIsUser(), PCArg('self', 'APPLY')), [AlreadyRegistered])
    def join(self):
        return Contestant.create(fields=DjangoStruct('Contestant')(contest=self, accepted=bool(Privilege.demand(self, 'JOIN')), name=token_container.token.user.login), user_list=[token_container.token.user])

    @ExportMethod(NoneType, [DjangoId('Contest'), DjangoId('User')], PCArg('self', 'MANAGE'))
    def add_admin(self, user):
        contestant = self.find_contestant(user)
        if contestant is None:
            Contestant.create(fields=DjangoStruct('Contestant')(contest=self, accepted=True, invisible=True, name=user.login), user_list=[user])
        else:
            contestant.invisible = True
            contestant.save()
#TODO: REJUDGE!
        Privilege.grant(user, self, 'MANAGE')
        Privilege.grant(user, self.contestant_role, 'MANAGE')

    @staticmethod
    def submit_to_result_to_render(submit):
        return ResultToRender(
        	submit=submit,
            problem=submit.problem.code,
            contestant=submit.contestant.usernames,
            status=submit.get_test_suite_status(),
            details=submit.get_test_suite_report()
            )

    @ExportMethod(ResultsToRender, [DjangoId('Contest'), DjangoId('ProblemMapping'), int, int], PCPermit())
    def get_all_results(self, problem=None, limit=20, offset=0):
        res = []
        q = Privilege.where_can(Submit.objects.filter(contestant__contest=self), 'OBSERVE')
        if problem:
        	q = q.filter(problem=problem)
        for submit in q.order_by('-id')[offset:offset+limit]:
        	res.append(Contest.submit_to_result_to_render(submit))
        return ResultsToRender(
            count=len(q),
            results=res
            )

    @ExportMethod(ResultsToRender, [DjangoId('Contest'), DjangoId('Contestant'), DjangoId('ProblemMapping'), int, int], PCPermit())
    def get_results(self, contestant, problem=None, limit=20, offset=0):
        res = []
        q = Privilege.where_can(Submit.objects.filter(contestant=contestant), 'OBSERVE')
        if problem:
        	q = q.filter(problem=problem)
        for submit in q.order_by('-id')[offset:offset+limit]:
        	res.append(Contest.submit_to_result_to_render(submit))
        return ResultsToRender(
            count=len(q),
            results=res
            )

    @staticmethod
    def contestant_to_contestant_to_render(contestant):
        return ContestantToRender(
        	contestant=contestant,
            name=contestant.usernames,
            members=contestant.get_member_users(),
            admin=any([Privilege.get(member, contestant.contest, 'MANAGE') for member in contestant.get_member_users()]),
            )

    @ExportMethod(ContestantsToRender, [DjangoId('Contest'), int, int], PCArg('self', 'VIEW'))
    def get_contestants(self, limit=20, offset=0):
        res = []
        q = Contestant.objects.filter(contest=self, accepted=True)
        for contestant in q.order_by('name')[offset:offset+limit]:
        	res.append(Contest.contestant_to_contestant_to_render(contestant))
        return ContestantsToRender(
            count=len(q),
            contestants=res
            )

    @ExportMethod(ContestantsToRender, [DjangoId('Contest'), int, int], PCArg('self', 'MANAGE'))
    def get_pending_contestants(self, limit=20, offset=0):
        res = []
        q = Contestant.objects.filter(contest=self, accepted=False)
        for contestant in q.order_by('name')[offset:offset+limit]:
        	res.append(Contest.contestant_to_contestant_to_render(contestant))
        return ContestantsToRender(
            count=len(q),
            contestants=res
            )

class ContestEvents(Events):
    model = Contest
    on_insert = on_update = ['name']
    on_delete = []
