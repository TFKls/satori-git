# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import Events
from satori.core.models._Object import Object

class OpenIdentity(Object):

    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_openidentity')

    identity = models.CharField(max_length=512, unique=True)
    user     = models.ForeignKey('User', related_name='authorized_openids')

    country  = models.CharField(max_length=64, null=True)
    email    = models.CharField(max_length=64, null=True)
    name     = models.CharField(max_length=64, null=True)
    language = models.CharField(max_length=64, null=True)

class OpenIdentityEvents(Events):
    model = OpenIdentity
    on_insert = on_update = ['identity', 'user']
    on_delete = []

