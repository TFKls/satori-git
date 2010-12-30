# vim:ts=4:sts=4:sw=4:expandtab

import crypt
import random
import string

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db              import models

from satori.core.dbev   import Events
from satori.core.models import Role, Session

LoginFailed = DefineException('LoginFailed', 'Invalid username or password')
InvalidLogin = DefineException('InvalidLogin', 'The specified login \'{login}\' is invalid: {reason}',
    [('login', unicode, False), ('reason', unicode, False)])
InvalidEmail = DefineException('InvalidEmail', 'The specified email \'{email}\' is invalid: {reason}',
    [('email', unicode, False), ('reason', unicode, False)])
InvalidPassword = DefineException('InvalidPassword', 'The specified password is invalid: {reason}',
    [('reason', unicode, False)])

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

    @staticmethod
    def login_ok(login):
        if not login:
            raise InvalidLogin(login=login, reason='is empty')
        if len(login) < 4:
            raise InvalidLogin(login=login, reason='is too short')
        if len(login) > 24:
            raise InvalidLogin(login=login, reason='is too long')
        try:
            login.decode('ascii')
        except:
            raise InvalidLogin(login=login, reason='contains invalid characters')
        for l in login:
            if not (l.islower() or l.isdigit() or l == '_'):
                raise InvalidLogin(login=login, reason='contains invalid characters')
        if not login[0].isalpha():
            raise InvalidLogin(login=login, reason='does not start with a letter')

    def password_ok(self, password):
        if password is None:
            return
        #TODO: python-crack?
        if len(password) < 4:
            raise InvalidPassword(reason='is too short')

    @staticmethod
    def email_ok(email):
        if email is None:
            return
        try:
            validate_email(email)
        except ValidationError:
            raise InvalidEmail(email=email, reason='is not RFC3696 compliant')

    @ExportMethod(NoneType, [unicode, unicode, unicode], PCPermit(), [InvalidLogin, InvalidPassword])
    @staticmethod
    def register(login, password, name):
        user = User()
        user.set_name(name)
        user.set_login(login)
        user.set_password(password)
        user.save()
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
        if self.password is None:
            return True
        return crypt.crypt(password, self.password) == self.password

    @ExportMethod(DjangoStruct('User'), [DjangoId('User'), unicode], PCArg('self', 'MANAGE'), [InvalidPassword])
    def set_password(self, password):
        self.password_ok(password)
        chars = string.letters + string.digits
        salt = random.choice(chars) + random.choice(chars)
        self.password = crypt.crypt(password, salt)
        self.save()
        return self

    @ExportMethod(DjangoStruct('User'), [DjangoId('User'), unicode], PCArg('self', 'MANAGE'), [InvalidLogin])
    def set_login(self, login):
        User.login_ok(login)
        try:
            User.objects.get(login=login)
            raise InvalidLogin(login=login, reason='is already used')
        except User.DoesNotExist:
            pass
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
