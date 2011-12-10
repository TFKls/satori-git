# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Role

@ExportModel
class SystemRole(Role):
    """Model. A Role that is used for internal system roles.
    """
    parent_role = models.OneToOneField(Role, parent_link=True, related_name='cast_systemrole')

    class ExportMeta(object):
        pass

    @staticmethod
    def create(fields):
        role = SystemRole()
        role.forbid_fields(fields, ['id', 'sort_field'])
        role.update_fields(fields, ['name'])
        role.name = role.name.strip()
        role.sort_field = role.name
        role.save()
        return role

    def modify(self, fields):
        self.forbid_fields(fields, ['id', 'sort_field'])
        self.update_fields(fields, ['name'])
        self.name = self.name.strip()
        self.sort_field = self.name
        self.save()
        return self

class SystemRoleEvents(Events):
    model = SystemRole
    on_insert = on_update = on_delete = []

