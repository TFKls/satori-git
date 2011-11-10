# vim:ts=4:sts=4:sw=4:expandtab

from datetime  import datetime
from types     import NoneType

from django.db import connection
from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity, Global

PrivilegeTimes = Struct('PrivilegeTimes', [
    ('start_on', datetime, True),
    ('finish_on', datetime, True),
    ])

@ExportClass(no_inherit=True)
class Privilege(Entity):
    """Model. Represents a single right on an object granted to a role.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_privilege')

    role          = models.ForeignKey('Role', related_name='privileges', on_delete=models.CASCADE)
    entity        = models.ForeignKey('Entity', related_name='privileged', on_delete=models.CASCADE)
    right         = models.CharField(max_length=64)
    start_on      = models.DateTimeField(null=True)
    finish_on     = models.DateTimeField(null=True)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('role', 'entity', 'right'),)

    @staticmethod
    def set_user_id(id):
        cursor = connection.cursor()
        cursor.callproc('set_user_id', [id])
        cursor.close()

    @staticmethod
    def update_user_rights():
        cursor = connection.cursor()
        cursor.callproc('update_user_rights', [])
        cursor.close()

    # BIG FAT WARNING
    # the returned queryset shouldn't be used in cirumstances causing table aliases change (subqueries, .exclude(), etc.)
    @staticmethod
    def wrap(queryset, struct=False, select=[], where=[]):
        if isinstance(queryset, type) and issubclass(queryset, models.Model):
            queryset = queryset.objects.all()

        for right in select:
            if not right in queryset.model._rights_meta.rights:
                raise RuntimeError('The specified right {0} is not available for model {1}'.format(right, quesyset.model.__name__))

        for right in where:
            if not right in queryset.model._rights_meta.rights:
                raise RuntimeError('The specified right {0} is not available for model {1}'.format(right, quesyset.model.__name__))

        select = set(select)
        if struct:
            select.update(queryset.model._struct_rights)

        where = set(where)

        do_select = {}
        do_where = []

        # create a copy of a queryset - prepare() modifies queryset.query
        queryset = queryset.all()

        for right in select:
            do_select['_can_' + right] = queryset.model._rights_meta.nodes[right].prepare(queryset.query).as_sql()

        for right in where:
            do_where.append(queryset.model._rights_meta.nodes[right].prepare(queryset.query).as_sql())

        return queryset.extra(select=do_select, where=do_where)

    @ExportMethod(NoneType, [DjangoId('Role'), DjangoId('Entity'), unicode, PrivilegeTimes], PCArg('entity', 'MANAGE'))
    @staticmethod
    def grant(role, entity, right, times=None):
        if not times:
            times = PrivilegeTimes()

        (priv, created) = Privilege.objects.get_or_create(role=role, entity=entity, right=right)
        priv.start_on = times.start_on
        priv.finish_on = times.finish_on
        priv.save()
        Privilege.update_user_rights()

    @ExportMethod(NoneType, [DjangoId('Role'), DjangoId('Entity'), unicode], PCArg('entity', 'MANAGE'))
    @staticmethod
    def revoke(role, entity, right):
        try:
            priv = Privilege.objects.get(role=role, entity=entity, right=right)
            priv.delete()
            Privilege.update_user_rights()
        except Privilege.DoesNotExist:
            pass

    @ExportMethod(PrivilegeTimes, [DjangoId('Role'), DjangoId('Entity'), unicode], PCOr(PCArg('entity', 'MANAGE'), PCTokenUser('role')))
    @staticmethod
    def get(role, entity, right):
        try:
            return Privilege.objects.get(role=role, entity=entity, right=right)
        except Privilege.DoesNotExist:
            return None

    @ExportMethod(TypedMap(DjangoStruct('Role'), PrivilegeTimes), [DjangoId('Entity'), unicode], PCArg('entity', 'MANAGE'))
    @staticmethod
    def list(entity, right):
        ret = {}
        for privilege in Privilege.objects.filter(entity=entity, right=right):
            ret[privilege.role] = privilege
        return ret

    @ExportMethod(bool, [DjangoId('Entity'), unicode], PCPermit())
    @staticmethod
    def demand(entity, right):
        model = models.get_model(*entity.model.split('.'))
        if not right in model._rights_meta.rights:
            raise RuntimeError('The specified right {0} is not available for model {1}'.format(right, model.__name__))

        if hasattr(entity, '_can_' + right):
            return getattr(entity, '_can_' + right)

        return Privilege.wrap(model, where=[right]).filter(id=entity.id).exists()

    @ExportMethod(NoneType, [DjangoId('Role'), unicode, PrivilegeTimes], PCGlobal('MANAGE_PRIVILEGES'))
    @staticmethod
    def global_grant(role, right, times=None):
        Privilege.grant(role, Global.get_instance(), right, times)

    @ExportMethod(NoneType, [DjangoId('Role'), unicode], PCGlobal('MANAGE_PRIVILEGES'))
    @staticmethod
    def global_revoke(role, right):
        Privilege.revoke(role, Global.get_instance(), right)

    @ExportMethod(PrivilegeTimes, [DjangoId('Role'), unicode], PCOr(PCGlobal('MANAGE_PRIVILEGES'), PCTokenUser('role')))
    @staticmethod
    def global_get(role, right):
        return Privilege.get(role, Global.get_instance(), right)

    @ExportMethod(TypedMap(DjangoStruct('Role'), PrivilegeTimes), [unicode], PCGlobal('MANAGE_PRIVILEGES'))
    @staticmethod
    def global_list(right):
        return Privilege.list(Global.get_instance(), right)
    
    @ExportMethod(bool, [unicode], PCPermit())
    @staticmethod
    def global_demand(right):
        return Privilege.demand(Global.get_instance(), right)

class PrivilegeEvents(Events):
    model = Privilege
    on_insert = on_update = on_delete = []
