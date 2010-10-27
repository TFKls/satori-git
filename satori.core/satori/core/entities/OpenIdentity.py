# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models

from satori.core.export        import ExportMethod
from satori.core.export_django import ExportModel
from satori.dbev               import Events

from satori.core.models import Entity

@ExportModel
class OpenIdentity(Entity):

    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Entity, parent_link=True, related_name='cast_openidentity')

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

