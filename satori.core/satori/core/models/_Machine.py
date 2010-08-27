# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import Events
from satori.core.models._User import User

class Machine(User):
    """Model. A Machine.
    """
    __module__ = "satori.core.models"
    parent_user = models.OneToOneField(User, parent_link=True, related_name='cast_machine')

    secret  = models.CharField(max_length=64)
    address = models.IPAddressField()
    netmask = models.IPAddressField(default='255.255.255.255')

class MachineEvents(Events):
    model = Machine
    on_insert = on_update = on_delete = []
