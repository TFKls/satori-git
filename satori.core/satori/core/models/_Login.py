# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._Object import Object

class Login(Object):

    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_login')

    login    = models.CharField(max_length=64, unique=True)
    password = models.CharField(max_length=128)
    user     = models.ForeignKey('User', related_name='authorized_logins')

class LoginEvents(events.Events):
    model = Login
    on_insert = on_update = ['login', 'user']
    on_delete = []
