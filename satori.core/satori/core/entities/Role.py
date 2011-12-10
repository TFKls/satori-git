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

    name          = models.CharField(max_length=256)
    sort_field    = models.CharField(max_length=256)
    children      = models.ManyToManyField('self', related_name='parents', through='RoleMapping', symmetrical=False)

    class ExportMeta(object):
        fields = [('name', 'VIEW'), ('sort_field', 'VIEW')]

    class RightsMeta(object):
        rights = ['EDIT']

        inherit_VIEW = ['EDIT']
        inherit_EDIT = ['MANAGE']

    @classmethod
    def inherit_rights(cls):
        inherits = super(Role, cls).inherit_rights()
        cls._inherit_add(inherits, 'EDIT', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'VIEW', 'id', 'EDIT')
        return inherits

    def __str__(self): #TODO
        return self.name

    def get_members(self):
        return self.children.all()

    def add_member(self, member):
        RoleMapping.objects.get_or_create(parent=self, child=member)[0].save()

    def delete_member(self, member):
        try:
            RoleMapping.objects.get(parent=self, child=member).delete()
        except RoleMapping.DoesNotExist:
            pass


class RoleEvents(Events):
    model = Role
    on_insert = on_update = ['name']
    on_delete = []
