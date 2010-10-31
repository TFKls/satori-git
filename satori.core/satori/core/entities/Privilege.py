# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from datetime  import datetime
from django.db import models
from types     import NoneType

from satori.core.dbev               import Events
from satori.core.export        import ExportClass, ExportMethod, Struct, PCGlobal, PCArg, token_container
from satori.core.export_django import DjangoId

from satori.core.models import Entity, Global


PrivilegeTimes = Struct('PrivilegeTimes', (
    ('start_on', datetime, True),
    ('finish_on', datetime, True),
))


@ExportClass
class Privilege(Entity):
    """Model. Represents a single right on an object granted to a role.
    """
    
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_privilege')

    role     = models.ForeignKey('Role', related_name='privileges')
    entity   = models.ForeignKey('Entity', related_name='privileged')
    right    = models.CharField(max_length=64)
    start_on  = models.DateTimeField(null=True)
    finish_on = models.DateTimeField(null=True)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('role', 'entity', 'right'),)

    @ExportMethod(NoneType, [DjangoId('Role'), DjangoId('Entity'), unicode, PrivilegeTimes], PCArg('entity', 'MANAGE_PRIVILEGES'))
    @staticmethod
    def grant(role, entity, right, times=PrivilegeTimes()):
        (priv, created) = Privilege.objects.get_or_create(role=role, entity=entity, right=right)
        priv.start_on = times.start_on
        priv.finish_on = times.finish_on
        priv.save()

    @ExportMethod(NoneType, [DjangoId('Role'), DjangoId('Entity'), unicode], PCArg('entity', 'MANAGE_PRIVILEGES'))
    @staticmethod
    def revoke(role, entity, right):
        try:
            priv = Privilege.objects.get(role=role, entity=entity, right=right)
            priv.delete()
        except Privilege.DoesNotExist:
            pass

    @ExportMethod(PrivilegeTimes, [DjangoId('Role'), DjangoId('Entity'), unicode], PCArg('entity', 'MANAGE_PRIVILEGES'))
    @staticmethod
    def get(role, entity, right):
        try:
            return Privilege.objects.get(role=role, entity=entity, right=right)
        except Privilege.DoesNotExist:
            return None

    @ExportMethod(bool, [DjangoId('Entity'), unicode], PCPermit())
    @staticmethod
    def demand(entity, right):
        from django.db import connection
        c = connection.cursor()
        c.callproc('right_check', [token_container.token.user_id, entity.id, str(right)])
        return bool(c.fetchall()[0][0])

    @ExportMethod(NoneType, [DjangoId('Role'), unicode, PrivilegeTimes], PCGlobal('MANAGE_PRIVILEGES'))
    @staticmethod
    def global_grant(role, right, times=PrivilegeTimes()):
        Privilege.grant(role, Global.get_instance(), right, times)

    @ExportMethod(NoneType, [DjangoId('Role'), unicode], PCGlobal('MANAGE_PRIVILEGES'))
    @staticmethod
    def global_revoke(role, right):
        Privilege.revoke(role, Global.get_instance(), right)

    @ExportMethod(PrivilegeTimes, [DjangoId('Role'), unicode], PCGlobal('MANAGE_PRIVILEGES'))
    @staticmethod
    def global_get(role, right):
        return Privilege.get(role, Global.get_instance(), right)

    @ExportMethod(bool, [unicode], PCPermit())
    @staticmethod
    def global_demand(right):
        return Privilege.demand(Global.get_instance(), right)

class PrivilegeEvents(Events):
    model = Privilege
    on_insert = on_update = on_delete = []
    
