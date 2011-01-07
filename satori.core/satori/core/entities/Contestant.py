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
    accepted    = models.BooleanField(default=False)
    invisible   = models.BooleanField(default=False)
    login       = models.CharField(max_length=64, unique=True)
    password    = models.CharField(max_length=128, null=True)

    class ExportMeta(object):
        fields = [('contest', 'VIEW'), ('accepted', 'VIEW'), ('invisible', 'VIEW')]

    @classmethod
    def inherit_rights(cls):
        inherits = super(Contestant, cls).inherit_rights()
        cls._inherit_add(inherits, 'VIEW', 'contest', 'VIEW')
        cls._inherit_add(inherits, 'MANAGE', 'contest', 'MANAGE')
        cls._inherit_add(inherits, 'OBSERVE', 'contest', 'OBSERVE')
        return inherits

    def update_usernames(self):
        name = ', '.join(x.name for x in self.get_member_users())
        if len(name) > 200:
            name = name[0:197] + '...'
        self.usernames = name;
        self.save()
        return self #TODO: Poinformowac przeliczanie rankingow

    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contestant'), bool], PCArg('self', 'MANAGE'))
    def set_accepted(self, accepted):
        self.accepted = accepted
        self.save()
        if accepted:
            self.contest.contestant_role.add_member(self)
        else:
            self.contest.contestant_role.delete_member(self)
        return self

    @ExportMethod(DjangoStructList('User'), [DjangoId('Contestant')], PCArg('self', 'VIEW'))
    def get_member_users(self):
        return User.objects.filter(parents=self)

    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contestant'), bool], PCArg('self', 'MANAGE'))
    def set_invisible(self, invisible):
        self.invisible = invisible
        self.save()
        return self #TODO: Poinformowac przeliczanie rankingow
    
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
        if contestant.check_password(password):
            session = Session.start()
            session.login(contestant, 'contestant')
            return str(token_container.token)
        else:
            raise LoginFailed()

    @ExportMethod(bool, [DjangoId('Contestant'), unicode], PCArg('self', 'EDIT'))
    def check_password(self, password):
        return password_check(self.password, password)

    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contestant'), unicode], PCArg('self', 'MANAGE'), [InvalidPassword])
    def set_password(self, password):
        password_ok(password)
        self.password = password_crypt(password)
        self.save()
        return self

    @ExportMethod(DjangoStruct('Contestant'), [DjangoId('Contestant'), unicode], PCArg('self', 'MANAGE'), [InvalidLogin])
    def set_login(self, login):
        login_ok(login)
        if Contestant.objects.filter(login=login, contest=self.contest):
            raise InvalidLogin(login=login, reason='is already used')
        self.login = login
        self.save()
        return self

    @ExportMethod(NoneType, [DjangoId('Contestant'), unicode, unicode], PCArg('self', 'EDIT'), [LoginFailed, InvalidPassword])
    def change_password(self, old_password, new_password):
        if not self.check_password(old_password):
            raise LoginFailed()
        self.set_password(new_password)


class ContestantEvents(Events):
    model = Contestant
    on_insert = on_update = ['name', 'contest']
    on_delete = []
