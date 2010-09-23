# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import Events
from satori.core.models._Object import Object
from satori.core.models._Global import Global

class Privilege(Object):
    """Model. Represents single right on object granted to the role.
    """
    __module__    = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_privilege')

    role     = models.ForeignKey('Role', related_name='privileges')
    object   = models.ForeignKey('Object', related_name='privileged')
    right    = models.CharField(max_length=64)
    startOn  = models.DateTimeField(null=True)
    finishOn = models.DateTimeField(null=True)

    #class Meta:                                                # pylint: disable-msg=C0111
    #    unique_together = (('role', 'object', 'right'),)

    @staticmethod
    def grant(role, object, right, start_on, finish_on):
        (priv, created) = Privilege.get_or_create(role=role, object=object, right=right)
        priv.startOn = start_on
        priv.finishOn = finish_on
        priv.save()

    @staticmethod
    def revoke(role, object, right):
        try:
            priv = Privilege.get(role=role, object=object, right=right)
            priv.delete()
        except:
            pass

    @staticmethod
    def global_grant(role, right, start_on, finish_on):
        Privilege.grant(role, Global.get_instance(), right, start_on, finish_on)

    @staticmethod
    def global_revoke(role, right):
        Privilege.global_revoke(role, Global.get_instance(), right)


class PrivilegeEvents(Events):
    model = Privilege
    on_insert = on_update = ['role', 'object', 'right']
    on_delete = []

