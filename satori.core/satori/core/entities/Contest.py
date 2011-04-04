# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.ars.server import server_info
from satori.core.dbev  import Events

from satori.core.models import Entity

AlreadyRegistered = DefineException('AlreadyRegistered', 'The specified user \'{login}\' is already registered',
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

    name            = models.CharField(max_length=64, unique=True)
    description     = models.TextField(blank=True, default="")
    problems        = models.ManyToManyField('Problem', through='ProblemMapping', related_name='contests')
    contestant_role = models.ForeignKey('Role', related_name='contest_contestants+')
    admin_role      = models.ForeignKey('Role', related_name='contest_admins+')
    archived        = models.BooleanField(default=False)

    lock_start   = models.DateTimeField(null=True)
    lock_finish  = models.DateTimeField(null=True)
    lock_address = models.IPAddressField(default='0.0.0.0')
    lock_netmask = models.IPAddressField(default='255.255.255.255')

    public_files = AttributeGroupField(PCArg('self', 'VIEW'), PCArg('self', 'MANAGE'), '')
    intra_files  = AttributeGroupField(PCArg('self', 'VIEW_INTRA_FILES'), PCArg('self', 'MANAGE'), '')

    class ExportMeta(object):
        fields = [('name', 'VIEW'), ('description', 'VIEW'), ('contestant_role', 'MANAGE'), ('admin_role', 'MANAGE'), ('lock_start', 'MANAGE'), ('lock_finish', 'MANAGE'), ('lock_address', 'MANAGE'), ('lock_netmask', 'MANAGE')]

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
        contest.forbid_fields(fields, ['id', 'contestant_role', 'admin_role'])
        contest.update_fields(fields, ['name', 'description', 'archived', 'lock_start', 'lock_finish', 'lock_address', 'lock_netmask'])
        contest.contestant_role = Role.create(fields=RoleStruct(name='Contestant of ' + contest.name))
        contest.admin_role = Role.create(fields=RoleStruct(name='Administrator of ' + contest.name))
        contest.save()
        contest.add_admin(token_container.token.user)
        Global.get_instance().contest_admins.add_member(contest.admin_role)
        Privilege.grant(contest.admin_role, contest, 'MANAGE')
        Privilege.grant(contest.admin_role, contest.admin_role, 'MANAGE')
        Privilege.grant(contest.admin_role, contest.contestant_role, 'MANAGE')
        Privilege.grant(contest.contestant_role, contest, 'VIEW')
        Privilege.grant(contest.contestant_role, contest, 'VIEW_INTRA_FILES')
        return contest
   
    @ExportMethod(DjangoStruct('Contest'), [DjangoId('Contest'), DjangoStruct('Contest')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, ['id', 'contestant_role', 'admin_role'])
        modified = self.update_fields(fields, ['name', 'description', 'archived', 'lock_start', 'lock_finish', 'lock_address', 'lock_netmask'])
        self.save()
        if 'name' in modified:
            self.contestant_role.modify(fields=RoleStruct(name='Contestant of ' + self.name))
            self.admin_role.modify(fields=RoleStruct(name='Administrator of ' + self.name))
        self.changed()
        return self

    @ExportMethod(NoneType, [DjangoId('Contest')], PCArg('self', 'MANAGE'))
    def disable_lock(self):
        self.lock_start = None
        self.lock_finish = None
        self.lock_address = '0.0.0.0'
        self.lock_netmask = '255.255.255.255'
        self.save()
    
    def changed(self):
        RawEvent().send(Event(type='checking_changed_contest', id=self.id))

    def changed_contestants(self):
        RawEvent().send(Event(type='checking_changed_contestants', id=self.id))

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
        return Contestant.create(fields=ContestantStruct(contest=self, accepted=bool(Privilege.demand(self, 'JOIN'))), user_list=[token_container.token.user])

    @ExportMethod(NoneType, [DjangoId('Contest'), DjangoId('User')], PCArg('self', 'MANAGE'))
    def add_admin(self, user):
        contestant = self.find_contestant(user)
        if contestant is None:
            contestant = Contestant.create(fields=ContestantStruct(contest=self, accepted=True, invisible=True), user_list=[user])
        else:
            contestant.modify(fields=ContestantStruct(accepted=True, invisible=True))
        self.admin_role.add_member(contestant)
        self.changed_contestants()

    @ExportMethod(NoneType, [DjangoId('Contest'), DjangoId('Role')], PCArg('self', 'MANAGE'))
    def delete_admin(self, role):
        contestant = self.find_contestant(role)
        if contestant is not None:
            self.admin_role.delete_member(contestant)
            contestant.modify(fields=ContestantStruct(invisible=False))

class ContestEvents(Events):
    model = Contest
    on_insert = on_update = ['name']
    on_delete = []
