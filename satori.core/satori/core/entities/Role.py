# vim:ts=4:sts=4:sw=4:expandtab

import logging

from django.db import models, DatabaseError

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class Role(Entity):
    """Model. Base for authorization "levels".
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_role')

    name          = models.CharField(max_length=50)
    children      = models.ManyToManyField('self', related_name='parents', through='RoleMapping', symmetrical=False)

    class ExportMeta(object):
        fields = [('name', 'VIEW')]

    @classmethod
    def inherit_rights(cls):
        inherits = super(Role, cls).inherit_rights()
        cls._inherit_add(inherits, 'EDIT', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'VIEW', 'id', 'EDIT')
        return inherits

    def __str__(self): #TODO
        return self.name

    @ExportMethod(DjangoStruct('Role'), [unicode, DjangoIdList('Role')], PCGlobal('MANAGE_PRIVILEGES'))
    @staticmethod
    def create(name, children=[]):
        res = Role(name=name)
        res.save()
        for child in children:
            res.add_member(child)
        Privilege.grant(token_container.token.role, res, 'MANAGE')
        return res

    #@ExportMethod(NoneType, [DjangoId('Role')], PCArg('self', 'MANAGE'))
    def delete(self):
        logging.error('role deleted') #TODO: Waiting for non-cascading deletes in django
        self.privileges.all().delete()
        self.children.all().delete()
        try:
            super(Role, self).delete()
        except DatabaseError:
            raise CannotDeleteObject()

    @ExportMethod(DjangoStruct('Role'), [DjangoId('Role'), unicode], PCArg('self', 'EDIT'))
    def set_name(self, name):
        self.name = name
        self.save()
        return self #TODO: poinformowac o zmianie nazwy kontestanta

    @ExportMethod(DjangoStructList('Role'), [DjangoId('Role')], PCArg('self', 'VIEW'))
    def get_members(self):
        return self.children.all()

    @ExportMethod(NoneType, [DjangoId('Role'), DjangoId('Role')], PCArg('self', 'MANAGE'))
    def add_member(self, member):
        RoleMapping.objects.get_or_create(parent=self, child=member)[0].save()

    @ExportMethod(NoneType, [DjangoId('Role'), DjangoId('Role')], PCArg('self', 'MANAGE'))
    def delete_member(self, member):
        try:
            RoleMapping.objects.get(parent=self, child=member).delete()
        except RoleMapping.DoesNotExist:
            pass

class RoleEvents(Events):
    model = Role
    on_insert = on_update = ['name']
    on_delete = []
