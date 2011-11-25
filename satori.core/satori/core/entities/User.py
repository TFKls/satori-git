# vim:ts=4:sts=4:sw=4:expandtab

import random
import string

from django.conf import settings
from django.core.mail import send_mail
from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Role, LoginFailed, InvalidLogin, login_ok, password_ok, password_crypt, password_check, password_rehash_old, email_ok

@ExportModel
class User(Role):
    """Model. A Role which can be logged onto.
    """
    parent_role = models.OneToOneField(Role, parent_link=True, related_name='cast_user')

    login       = models.CharField(max_length=64, unique=True)
    password    = models.CharField(max_length=128, null=True)
    email       = models.CharField(max_length=64, null=True)
    firstname   = models.CharField(max_length=64, null=True)
    lastname    = models.CharField(max_length=64, null=True)
    affiliation = models.CharField(max_length=64, null=True)
    confirmed   = models.BooleanField(default=False)
    activated   = models.BooleanField(default=True)
    activation_code = models.CharField(max_length=128, null=True, unique=True)

    profile     = AttributeGroupField(PCArg('self', 'EDIT'), PCArg('self', 'EDIT'), '')

    class ExportMeta(object):
        fields = [('login', 'VIEW'), ('email', 'EDIT'), ('firstname', 'VIEW'), ('lastname', 'VIEW'), ('activated', 'VIEW'), ('confirmed', 'VIEW'), ('affiliation', 'VIEW')]
    
    def save(self, *args, **kwargs):
        self.fixup_profile()
        login_ok(self.login)
        email_ok(self.email)
        self.name = u' '.join([self.firstname, self.lastname]).strip()
        self.sort_field = u' '.join([self.lastname, self.firstname]).strip()
        if User.objects.filter(login=self.login).exclude(id=self.id):
            raise InvalidLogin(login=self.login, reason='is already used')
        super(User, self).save(*args, **kwargs)

    @ExportMethod(DjangoStruct('User'), [DjangoStruct('User')], PCGlobal('MANAGE'), [InvalidLogin, InvalidEmail, CannotSetField])
    @staticmethod
    def create(fields):
        user = User()
        user.forbid_fields(fields, ['id', 'name', 'sort_field'])
        modified = user.update_fields(fields, ['login', 'email', 'firstname', 'lastname', 'confirmed', 'activated', 'activation_code'])
        if not 'activation_code' in modified:
            user.activation_code = ''.join([random.choice(string.letters + string.digits) for i in range(16)])
        user.save()
        Privilege.grant(user, user, 'EDIT')
        Privilege.grant(Global.get_instance().authenticated, user, 'VIEW')
        Global.get_instance().authenticated.add_member(user)
        return user
        
    @ExportMethod(NoneType, [DjangoStruct('User'), unicode, TypedMap(unicode, AnonymousAttribute)], PCEachValue('profile', PCRawBlob('item')), [InvalidLogin, InvalidPassword, InvalidEmail, CannotSetField])
    @staticmethod
    def register(fields, password, profile={}):
        fields.activated = not settings.ACTIVATION_REQUIRED
        fields.confirmed = False
        user = User.create(fields)
        user.set_password(password)
        user.profile_set_map(profile)
        if settings.ACTIVATION_REQUIRED:
            send_mail(settings.ACTIVATION_EMAIL_SUBJECT, 
                unicode(settings.ACTIVATION_EMAIL_BODY).format(code=user.activation_code, name=user.name),
                settings.ACTIVATION_EMAIL_FROM, 
                [user.email])

    @ExportMethod(DjangoStruct('User'), [DjangoId('User'), DjangoStruct('User')], PCArg('self', 'EDIT'), [CannotSetField, InvalidLogin, InvalidEmail])
    def modify(self, fields):
        changed = []
        if Privilege.demand(self, 'MANAGE'):
            self.forbid_fields(fields, ['id', 'name', 'sort_field'])
            changed = self.update_fields(fields, ['login', 'email', 'firstname', 'lastname', 'confirmed', 'activated', 'activation_code'])
        else:
            self.forbid_fields(fields, ['id', 'name', 'sort_field', 'login', 'confirmed', 'activated', 'activation_code', 'email'])
            if self.confirmed:
                self.forbid_fields(fields, ['firstname', 'lastname'])
            else:
                change = self.update_fields(fields, ['firstname', 'lastname'])
        self.save()
        if 'firstname' in changed or 'lastname' in changed:
            for c in Contestant.objects.filter(children=self):
                c.update_usernames()
        return self

    @ExportMethod(NoneType, [unicode], PCPermit())
    def activate(activation_code):
        user = User.objects.get(activation_code=activation_code)
        user.activated = True
        user.save()

    @ExportMethod(unicode, [unicode, unicode], PCPermit(), [LoginFailed])
    @staticmethod
    def authenticate(login, password):
        try:
            user = User.objects.get(login=login)
        except User.DoesNotExist:
            raise LoginFailed()
        if not user.activated:
            raise LoginFailed()
        if password_check(user.password, password):
            session = Session.start()
            session.login(user, 'user')
            pwhash = password_rehash_old(user.password, password)
            if pwhash != user.password:
            	user.password = pwhash
            	user.save()
            return str(token_container.token)
        else:
            raise LoginFailed()
    
    @ExportMethod(NoneType, [DjangoId('User'), unicode], PCArg('self', 'MANAGE'), [InvalidPassword])
    def set_password(self, new_password):
        password_ok(new_password)
        self.password = password_crypt(new_password)
        self.save()

    @ExportMethod(NoneType, [DjangoId('User'), unicode, unicode], PCArg('self', 'EDIT'), [LoginFailed, InvalidPassword])
    def change_password(self, old_password, new_password):
        if not password_check(self.password, old_password):
            raise LoginFailed()
        password_ok(new_password)
        self.password = password_crypt(new_password)
        self.save()

class UserEvents(Events):
    model = User
    on_insert = on_update = ['name']
    on_delete = []
