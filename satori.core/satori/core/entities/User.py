# vim:ts=4:sts=4:sw=4:expandtab

import crypt
from   django.db import models
import random
import string

from satori.core.dbev               import Events

from satori.core.models import Role

LoginFailed = DefineException('LoginFailed', 'Invalid username or password')
InvalidLogin = DefineException('InvalidLogin', 'The specified login \'{login}\' is invalid: {reason}',
    [('login', unicode, False), ('reason', unicode, False)])

@ExportModel
class User(Role):
    """Model. A Role which can be logged onto.
    """

    parent_role = models.OneToOneField(Role, parent_link=True, related_name='cast_user')

    login     = models.CharField(max_length = 64, unique=True)
    password  = models.CharField(max_length=128)

    class ExportMeta(object):
        fields = [('login', 'VIEW')]

    @staticmethod
    def login_ok(login):
        if len(login) < 4:
            raise InvalidLogin(login=login, reason='is too short')
        if len(login) > 24:
            raise InvalidLogin(login=login, reason='is too long')
        try:
            login.decode('ascii')
        except:
            raise InvalidLogin(login=login, reason='contains invalid characters')
        count = 0
        for l in login:
            if not (l.isalpha() or l.isdigit() or l == '_'):
                raise InvalidLogin(login=login, reason='contains invalid characters')
            if l.isalpha() and l.islower():
            	count += 1
        if not login[0].isalpha():
            raise InvalidLogin(login=login, reason='does not start with a letter')
        if count == 0:
            raise InvalidLogin(login=login, reason='does not contain a lowercase letter')
        return True

    @staticmethod
    def password_ok(password): #TODO: python-crack?
        return True

    @ExportMethod(NoneType, [unicode, unicode, unicode], PCPermit(), [InvalidLogin])
    @staticmethod
    def register(login, password, name):
        if not login:
            raise InvalidLogin(login=login, reason='is empty')
        
        User.login_ok(login)

        try:
            User.objects.get(login=login)
            raise InvalidLogin(login=login, reason='is already used')
        except User.DoesNotExist:
            pass

        user = User(login=login, name=name)
        user.save()
        user.set_password(password)
        Privilege.grant(user, user, 'MANAGE')

    @ExportMethod(unicode, [unicode, unicode], PCPermit(), [LoginFailed])
    @staticmethod
    def authenticate(login, password):
        try:
            user = User.objects.get(login=login)
        except User.DoesNotExist:
            raise LoginFailed()
        if user.check_password(password):
            return str(Token(user=user, auth='login', validity=timedelta(hours=6)))
        else:
            raise LoginFailed()

    @ExportMethod(bool, [DjangoId('User'), unicode], PCOr(PCTokenUser('self'), PCArg('self', 'MANAGE')))
    def check_password(self, password):
        return crypt.crypt(password, self.password) == self.password

    @ExportMethod(NoneType, [DjangoId('User'), unicode], PCArg('self', 'MANAGE'))
    def set_password(self, password):
        chars = string.letters + string.digits
        salt = random.choice(chars) + random.choice(chars)
        self.password = crypt.crypt(password, salt)

    @ExportMethod(NoneType, [DjangoId('User'), unicode, unicode], PCOr(PCTokenUser('self'), PCArg('self', 'MANAGE')), [LoginFailed])
    def change_password(self, old_password, new_password):
        if not self.check_password(old_password):
            raise LoginFailed()

        self.set_password(new_password)

class UserEvents(Events):
    model = User
    on_insert = on_update = ['name']
    on_delete = []

