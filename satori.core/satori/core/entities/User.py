# vim:ts=4:sts=4:sw=4:expandtab

from django.db              import models

from satori.core.dbev   import Events
from satori.core.models import Role, Session, LoginFailed, InvalidLogin, login_ok, password_ok, password_crypt, password_check, email_ok

@ExportModel
class User(Role):
    """Model. A Role which can be logged onto.
    """
    parent_role = models.OneToOneField(Role, parent_link=True, related_name='cast_user')

    login       = models.CharField(max_length=64, unique=True)
    password    = models.CharField(max_length=128, null=True)
    email       = models.CharField(max_length=128, null=True)

    class ExportMeta(object):
        fields = [('login', 'VIEW'), ('email', 'EDIT')]

    @ExportMethod(NoneType, [unicode, unicode, unicode], PCPermit(), [InvalidLogin, InvalidPassword])
    @staticmethod
    def register(login, password, name):
        user = User()
        user.set_name(name)
        user.set_login(login)
        user.set_password(password)
        user.save()
        Global.get_instance().authenticated.add_member(user)
        Privilege.grant(user, user, 'EDIT')

    @ExportMethod(unicode, [unicode, unicode], PCPermit(), [LoginFailed])
    @staticmethod
    def authenticate(login, password):
        try:
            user = User.objects.get(login=login)
        except User.DoesNotExist:
            raise LoginFailed()
        if user.check_password(password):
            session = Session.start()
            session.login(user, 'user')
            return str(token_container.token)
        else:
            raise LoginFailed()

    @ExportMethod(bool, [DjangoId('User'), unicode], PCArg('self', 'EDIT'))
    def check_password(self, password):
        return password_check(self.password, password)

    @ExportMethod(DjangoStruct('User'), [DjangoId('User'), unicode], PCArg('self', 'MANAGE'), [InvalidPassword])
    def set_password(self, password):
        password_ok(password)
        self.password = password_crypt(password)
        self.save()
        return self

    @ExportMethod(DjangoStruct('User'), [DjangoId('User'), unicode], PCArg('self', 'MANAGE'), [InvalidLogin])
    def set_login(self, login):
        login_ok(login)
        if User.objects.filter(login=login):
            raise InvalidLogin(login=login, reason='is already used')
        self.login = login
        self.save()
        return self

    @ExportMethod(NoneType, [DjangoId('User'), unicode, unicode], PCArg('self', 'EDIT'), [LoginFailed, InvalidPassword])
    def change_password(self, old_password, new_password):
        if not self.check_password(old_password):
            raise LoginFailed()
        self.set_password(new_password)

class UserEvents(Events):
    model = User
    on_insert = on_update = ['name']
    on_delete = []
