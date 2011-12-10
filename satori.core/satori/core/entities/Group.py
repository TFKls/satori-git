# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Role

@ExportModel
class Group(Role):
    """Model. A Role which can contain other roles.
    """
    parent_role = models.OneToOneField(Role, parent_link=True, related_name='cast_group')

    class ExportMeta(object):
        pass

    @ExportMethod(DjangoStruct('Group'), [DjangoStruct('Group'), DjangoIdList('Role')], PCGlobal('MANAGE_PRIVILEGES'), [CannotSetField])
    @staticmethod
    def create(fields, children=[]):
        group = Group()
        group.forbid_fields(fields, ['id', 'sort_field'])
        group.update_fields(fields, ['name'])
        group.name = group.name.strip()
        group.sort_field = group.name
        group.save()
        for child in children:
            group.add_member(child)
        Privilege.grant(token_container.token.role, group, 'MANAGE')
        return group

    @ExportMethod(DjangoStruct('Group'), [DjangoId('Group'), DjangoStruct('Group')], PCArg('self', 'EDIT'), [CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, ['id', 'sort_field'])
        self.update_fields(fields, ['name'])
        self.name = self.name.strip()
        self.sort_field = self.name
        self.save()
        return self
        
    @ExportMethod(NoneType, [DjangoId('Group')], PCArg('self', 'MANAGE'), [CannotDeleteObject])
    def delete(self):
        try:
            super(Group, self).delete()
        except models.ProtectedError as e:
            raise CannotDeleteObject()

    @ExportMethod(DjangoStructList('Role'), [DjangoId('Group')], PCArg('self', 'VIEW'))
    def get_members(self):
        return super(Group, self).get_members()

    @ExportMethod(NoneType, [DjangoId('Group'), DjangoId('Role')], PCArg('self', 'MANAGE'))
    def add_member(self, member):
        super(Group, self).add_member(member)

    @ExportMethod(NoneType, [DjangoId('Group'), DjangoId('Role')], PCArg('self', 'MANAGE'))
    def delete_member(self, member):
        super(Group, self).delete_member(member)


class GroupEvents(Events):
    model = Group
    on_insert = on_update = on_delete = []
