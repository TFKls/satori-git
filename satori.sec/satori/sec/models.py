# vim:ts=4:sts=4:sw=4:expandtab

__all__ = (
    'Nonce',
    'Association',
    'Login',
    'OpenIdentity'
)

from django.db import models
from satori.dbev import events
from satori.ars import django_
from satori.core.models import User, Object

class Nonce(models.Model):

    __module__ = "satori.sec.models"

    server_url = models.CharField(max_length=2047)
    timestamp  = models.IntegerField()
    salt       = models.CharField(max_length=40)

    class Meta:
        unique_together = (('server_url', 'timestamp', 'salt'),)

class Association(models.Model):

    __module__ = "satori.sec.models"

    server_url = models.CharField(max_length=2047)
    handle     = models.CharField(max_length=255)
    secret     = models.CharField(max_length=511)
    issued     = models.IntegerField()
    lifetime   = models.IntegerField()
    assoc_type = models.CharField(max_length=64)

    class Meta:
        unique_together = (('server_url', 'handle'),)

class Login(Object):

    __module__ == "satori.sec.models"

    login    = models.CharField(max_length=64, unique=True)
    password = models.CharField(max_length=128)
    user     = models.ForeignKey(User, related_name='authorized_logins')

class LoginEvents(events.Events):
    model = Login
    on_insert = on_update = ['login', 'user']
    on_delete = []

class LoginOpers(django_.Opers):
    login = django_.ModelProceduresProvider(Login)

class OpenIdentity(Object):

    __module__ == "satori.sec.models"

    identity = models.CharField(max_length=512, unique=True)
    user     = models.ForeignKey(User, related_name='authorized_openids')

class OpenIdentityEvents(events.Events):
    model = OpenIdentity
    on_insert = on_update = ['identity', 'user']
    on_delete = []

class OpenIdentityOpers(django_.Opers):
    openidentity = django_.ModelProceduresProvider(OpenIdentity)

