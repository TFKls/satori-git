from django.db import models
from satori.dbev import events
from satori.ars import django2ars
from satori.core.models._Object import Object

class Role(Object):
    """Model. Base for authorization "levels".
    """
    __module__ = "satori.core.models"

    name        = models.CharField(max_length=50)
    absorbing   = models.BooleanField(default=False)

class RoleEvents(events.Events):
    model = Role
    on_insert = on_update = ['name']
    on_delete = []

class RoleOpers(django2ars.Opers):
    role = django2ars.ModelOpers(Role)

