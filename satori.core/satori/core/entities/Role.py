# vim:ts=4:sts=4:sw=4:expandtab

#! module models

from django.db import models

from satori.core.export        import ExportMethod, PCArg
from satori.core.export_django import ExportModel, DjangoStructList, DjangoId
from satori.core.dbev               import Events

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

    @ExportMethod(DjangoStructList('Role'), [DjangoId('Role')], PCArg('self', 'VIEW'))
    def get_members(self):
        return self.children.all()

    @ExportMethod(NoneType, [DjangoId('Role'), DjangoId('Role')], PCArg('self', 'EDIT'))
    def add_member(self, member):
        RoleMapping.objects.get_or_create(parent=self, child=member)[0].save()

    @ExportMethod(NoneType, [DjangoId('Role'), DjangoId('Role')], PCArg('self', 'EDIT'))
    def delete_member(self, member):
        try:
            RoleMapping.objects.get(parent=self, child=member).delete()
        except RoleMapping.DoesNotExist:
            pass

    def __str__(self):
        return self.name

class RoleEvents(Events):
    model = Role
    on_insert = on_update = ['name']
    on_delete = []

