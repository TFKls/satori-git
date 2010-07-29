from django.db import models
from satori.dbev import events
from satori.ars import wrapper
from satori.core import cwrapper
from satori.core.models._Object import Object
#from satori.core.models._RoleRel import RoleRel

class Role(Object):
    """Model. Base for authorization "levels".
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_role')

    name        = models.CharField(max_length=50)
    absorbing   = models.BooleanField(default=False)
    startOn     = models.DateTimeField(null=True)
    finishOn    = models.DateTimeField(null=True)
    children    = models.ManyToManyField("self", related_name='parents', through='RoleMapping', symmetrical=False)

class RoleEvents(events.Events):
    model = Role
    on_insert = on_update = ['name']
    on_delete = []

class RoleWrapper(wrapper.WrapperClass):
    role = cwrapper.ModelWrapper(Role)

