# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.ars import wrapper
from satori.core import cwrapper
from satori.core.models._User import User
from satori.core.models._Object import Object

class OpenIdentity(Object):

    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_openidentity')

    identity = models.CharField(max_length=512, unique=True)
    user     = models.ForeignKey(User, related_name='authorized_openids')

class OpenIdentityEvents(events.Events):
    model = OpenIdentity
    on_insert = on_update = ['identity', 'user']
    on_delete = []

class OpenIdentityWrapper(wrapper.WrapperClass):
    openidentity = cwrapper.ModelWrapper(OpenIdentity)
