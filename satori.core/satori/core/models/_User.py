# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._Role import Role

class User(Role):
    """Model. A Role which can be logged onto.
    """
    __module__ = "satori.core.models"
    parent_role = models.OneToOneField(Role, parent_link=True, related_name='cast_user')

    login      = models.CharField(max_length = 64, unique=True)
    fullname   = models.CharField(max_length = 64)
    def __unicode__(self):
        return self.fullname

    # add validation

class UserEvents(events.Events):
    model = User
    on_insert = on_update = ['name']
    on_delete = []

