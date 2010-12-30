# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.ars.server import server_info
from satori.core.dbev  import Events

from satori.core.models import Entity

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

    name        = models.CharField(max_length=50, unique=True)
    problems    = models.ManyToManyField('Problem', through='ProblemMapping', related_name='contests')
    contestant_role = models.ForeignKey('Role', related_name='+')
    archived    = models.BooleanField(default=False)

    lock_start  = models.DateTimeField(null=True)
    lock_finish = models.DateTimeField(null=True)
    lock_address = models.IPAddressField(default='0.0.0.0')
    lock_netmask = models.IPAddressField(default='255.255.255.255')

    public_files = AttributeGroupField(PCArg('self', 'VIEW'), PCArg('self', 'MANAGE'), '')
    intra_files = AttributeGroupField(PCArg('self', 'VIEW_INTRA_FILES'), PCArg('self', 'MANAGE'), '')

    class ExportMeta(object):
        fields = [('name', 'VIEW'), ('contestant_role', 'MANAGE'), ('lock_start', 'MANAGE'), ('lock_finish', 'MANAGE'), ('lock_address', 'MANAGE'), ('lock_netmask', 'MANAGE')]

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
                if (ipaddr.IPv4Address(server_info.client_ip) in ipaddr.IPv4Network(contest.lock_address + '/' + contest.lock_netmask))]
        
        if len(contests) == 0:
            return None
        if len(contests) > 1:
            raise Contest.MultipleObjectsReturned()
        else:
            return contests[0]
        
    @classmethod
    def inherit_rights(cls):
        inherits = super(Contest, cls).inherit_rights()
        cls._inherit_add(inherits, 'OBSERVE', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'VIEW_TASKS', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'VIEW_INTRA_FILES', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'APPLY', 'id', 'JOIN')
        cls._inherit_add(inherits, 'JOIN', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'SUBMIT', 'id', 'MANAGE')
        return inherits

    @ExportMethod(DjangoStruct('Contest'), [unicode], PCAnd(PCTokenIsUser(), PCGlobal('MANAGE_CONTESTS')))
    @staticmethod
    def create_contest(name):
        r = Role()
        r.name = 'Contestant of ' + name
        r.save()
        
        c = Contest()
        c.name = name
        c.contestant_role = r
        c.save()

        Privilege.grant(token_container.token.role, c, 'MANAGE')
        Privilege.grant(r, c, 'VIEW')

        return c
    
    @ExportMethod(DjangoStruct('Contest'), [DjangoId('Contest'), unicode], PCArg('self', 'MANAGE'))
    def set_name(self, name):
        self.name = name
        self.save()

        self.contestant_role.name = 'Contestant of ' + name
        self.contestant_role.save()

        return self

    @ExportMethod(DjangoStruct('Contest'), [DjangoId('Contest'), datetime, datetime, unicode, unicode], PCArg('self', 'MANAGE'))
    def set_lock(self, start, finish, address, netmask):
        self.lock_start = start
        self.lock_finish = finish
        self.lock_address = address
        self.lock_netmask = netmask
        self.save()

        return self

    @ExportMethod(DjangoStruct('Contest'), [DjangoId('Contest')], PCArg('self', 'MANAGE'))
    def set_no_lock(self):
        self.lock_start = None
        self.lock_finish = None
        self.lock_address = '0.0.0.0'
        self.lock_netmask = '255.255.255.255'
        self.save()

        return self

    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contest'), DjangoId('Role')], PCOr(PCTokenUser('user'), PCArg('self', 'MANAGE')))
    def find_contestant(self, user):
        try:
            return Contestant.objects.get(contest=self, children__id=user.id)
        except Contestant.DoesNotExist:
            try:
                return Contestant.objects.get(contest=self, id=user.id)
            except Contestant.DoesNotExist:
               return None

    # TODO: check if exists
    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contest'), DjangoIdList('User')], PCArg('self', 'MANAGE'))
    def create_contestant(self, user_list):
        c = Contestant()
        c.contest = self
        c.save()

        c.set_accepted(True)
        for user in user_list:
            c.add_member(user)
            
        Privilege.grant(c, c, 'OBSERVE')

        return c

    # TODO: check if exists
    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contest')], PCAnd(PCTokenIsUser(), PCArg('self', 'APPLY')))
    def join_contest(self):
        c = Contestant()
        c.contest = self
        c.save()

        c.set_accepted(bool(Privilege.demand(self, 'JOIN')))
        c.add_member(token_container.token.user)

        Privilege.grant(c, c, 'OBSERVE')

        return c

    @ExportMethod(DjangoStruct('Submit'), [DjangoId('Contest'), DjangoId('ProblemMapping'), unicode, unicode], PCArg('problem_mapping', 'SUBMIT'))
    def submit(self, problem_mapping, content, filename):
        contestant = self.find_contestant(token_container.token.role)
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

        RawEvent().send(Event(type='checking_new_submit', id=submit.id))
        return submit

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
    @staticmethod
    def submit_to_result_to_render(submit):
        return ResultToRender(
        	submit=submit,
            problem=submit.problem.code,
            contestant=submit.contestant.name_auto(),
            status=submit.get_test_suite_status(),
            details=submit.get_test_suite_report()
            )

    #TODO: OBSERVE on submits
    @ExportMethod(ResultsToRender, [DjangoId('Contest'), DjangoId('ProblemMapping'), int, int], PCArg('self', 'OBSERVE'))
    def get_all_results(self, problem=None, limit=20, offset=0):
        res = []
        q = Submit.objects.filter(contestant__contest=self)
        if problem:
        	q = q.filter(problem=problem)
        for submit in q.order_by('-id')[offset:offset+limit]:
        	res.append(Contest.submit_to_result_to_render(submit))
        return {
            'count' : len(q),
            'results'  : res,
        }

    #TODO: OBSERVE on submits
    @ExportMethod(ResultsToRender, [DjangoId('Contest'), DjangoId('Contestant'), DjangoId('ProblemMapping'), int, int], PCArg('contestant', 'OBSERVE'))
    def get_results(self, contestant, problem=None, limit=20, offset=0):
        res = []
        q = Submit.objects.filter(contestant=contestant)
        if problem:
        	q = q.filter(problem=problem)
        for submit in q.order_by('-id')[offset:offset+limit]:
        	res.append(Contest.submit_to_result_to_render(submit))
        return {
            'count' : len(q),
            'results'  : res,
        }

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
    @staticmethod
    def contestant_to_contestant_to_render(contestant):
        return {
        	'contestant' : contestant,
            'name' : contestant.name_auto(),
            'members' : contestant.get_member_users(),
            'admin' : any([Privilege.get(member, contestant.contest, 'MANAGE') for member in contestant.get_member_users()])
            }

    @ExportMethod(ContestantsToRender, [DjangoId('Contest'), int, int], PCArg('self', 'VIEW'))
    def get_contestants(self, limit=20, offset=0):
        res = []
        q = Contestant.objects.filter(contest=self, accepted=True)
        for contestant in q.order_by('name')[offset:offset+limit]:
        	res.append(Contest.contestant_to_contestant_to_render(contestant))
        return {
            'count' : len(q),
            'contestants'  : res,
        }

    @ExportMethod(ContestantsToRender, [DjangoId('Contest'), int, int], PCArg('self', 'MANAGE'))
    def get_pending_contestants(self, limit=20, offset=0):
        res = []
        q = Contestant.objects.filter(contest=self, accepted=False)
        for contestant in q.order_by('name')[offset:offset+limit]:
        	res.append(Contest.contestant_to_contestant_to_render(contestant))
        return {
            'count' : len(q),
            'contestants'  : res,
        }

class ContestEvents(Events):
    model = Contest
    on_insert = on_update = ['name']
    on_delete = []

