# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Role, LoginFailed, InvalidLogin, login_ok, password_ok, password_crypt, password_check

@ExportModel
class Contestant(Role):
    """Model. A Role for a contest participant.
    """
    parent_role = models.OneToOneField(Role, parent_link=True, related_name='cast_contestant')

    usernames   = models.CharField(max_length=200)
    contest     = models.ForeignKey('Contest', related_name='contestants')
    accepted    = models.BooleanField(default=True)
    invisible   = models.BooleanField(default=False)
    login       = models.CharField(max_length=64, null=True)
    password    = models.CharField(max_length=128, null=True)
    
    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'login'),)

    class ExportMeta(object):
        fields = [('contest', 'VIEW'), ('accepted', 'VIEW'), ('invisible', 'VIEW'), ('login', 'VIEW')]

    @classmethod
    def inherit_rights(cls):
        inherits = super(Contestant, cls).inherit_rights()
        cls._inherit_add(inherits, 'VIEW', 'contest', 'VIEW')
        cls._inherit_add(inherits, 'OBSERVE', 'contest', 'OBSERVE')
        cls._inherit_add(inherits, 'MANAGE', 'contest', 'MANAGE')
        return inherits

    def save(self, *args, **kwargs):
        if self.login is not None:
            login_ok(self.login)
            if Contestant.objects.filter(login=self.login, contest=self.contest).exclude(id=self.id):
                raise InvalidLogin(login=self.login, reason='is already used')
        super(Contestant, self).save(*args, **kwargs)

    @ExportMethod(DjangoStruct('Contestant'), [DjangoStruct('Contestant'), DjangoIdList('User')], PCArgField('fields', 'contest', 'MANAGE'), [AlreadyRegistered, InvalidLogin, InvalidPassword, CannotSetField])
    @staticmethod
    def create(fields, user_list):
        contestant = Contestant()
        contestant.forbid_fields(fields, ['usernames'])
        modified = contestant.update_fields(fields, ['contest', 'accepted', 'invisible', 'login'])
        contestant.save()
        Privilege.grant(contestant, contestant, 'OBSERVE')
        for user in user_list:
            if contestant.contest.find_contestant(user):
                raise AlreadyRegistered(login=user.login)
            contestant.add_member(user)
        if contestant.accepted:
            contestant.contest.contestant_role.add_member(contestant)
        return contestant

    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contestant'), DjangoStruct('Contestant')], PCArg('self', 'MANAGE'), [InvalidLogin, InvalidPassword, CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, ['id', 'usernames', 'contest'])
        modified = self.update_fields(fields, ['accepted', 'invisible', 'login'])
        self.save()
        if 'accepted' in modified:
            if self.accepted:
                self.contest.contestant_role.add_member(self)
            else:
                self.contest.contestant_role.delete_member(self)
        return self

    def update_usernames(self):
        name = ', '.join(x.name for x in self.get_member_users())
        if len(name) > 200:
            name = name[0:197] + '...'
        self.usernames = name;
        self.save()
        return self #TODO: Poinformowac przeliczanie rankingow

    @ExportMethod(DjangoStructList('User'), [DjangoId('Contestant')], PCArg('self', 'VIEW'))
    def get_member_users(self):
        return User.objects.filter(parents=self)

    @ExportMethod(unicode, [unicode, unicode], PCPermit(), [LoginFailed])
    @staticmethod
    def authenticate(login, password):
        contest = Contest.get_current_lock()
        if contest is None:
            raise LoginFailed()
        try:
            contestant = Contestant.objects.get(login=login, contest=contest)
        except Contestant.DoesNotExist:
            raise LoginFailed()
        if password_check(contestant.password, password):
            session = Session.start()
            session.login(contestant, 'contestant')
            return str(token_container.token)
        else:
            raise LoginFailed()

    @ExportMethod(NoneType, [DjangoId('Contestant'), unicode], PCArg('self', 'MANAGE'), [InvalidPassword])
    def set_password(self, new_password):
        password_ok(new_password)
        self.password = password_crypt(new_password)
        self.save()

    @ExportMethod(NoneType, [DjangoId('Contestant'), unicode, unicode], PCArg('self', 'EDIT'), [LoginFailed, InvalidPassword])
    def change_password(self, old_password, new_password):
        if not password_check(self.password, old_password):
            raise LoginFailed()
        password_ok(new_password)
        self.password = password_crypt(new_password)
        self.save()

class ContestantEvents(Events):
    model = Contestant
    on_insert = on_update = ['name', 'contest']
    on_delete = []
