# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._Object import Object

class Privilege(Object):
    """Model. Represents single right on object granted to the role.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_privilege')

    role    = models.ForeignKey('Role', related_name='privileges')
    object  = models.ForeignKey('Object', related_name='privileged')
    right   = models.CharField(max_length=64)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('role', 'object', 'right'),)

class PrivilegeEvents(events.Events):
    model = Privilege
    on_insert = on_update = ['role', 'object', 'right']
    on_delete = []

