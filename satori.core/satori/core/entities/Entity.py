# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models
from satori.core.dbev import Events
from satori.core.export import ExportMethod, PCPermit
from satori.core.export_django import ExportModel, DjangoId, generate_attribute_group

@ExportModel
class Entity(models.Model):
    """Model. Base for all database objects. Provides common GUID space.
    """
    __module__ = "satori.core.models"

    model = models.CharField(max_length=64, editable=False)

    generate_attribute_group('Entity', None, 'ATTRIBUTE_READ', 'ATTRIBUTE_WRITE', globals(), locals())

    def save(self, *args, **kwargs):
        if not self.model:
              self.model = self._meta.app_label + '.' + self._meta.module_name
        super(Entity, self).save(*args, **kwargs)

    def inherit_right(self, right):
        from satori.core.models import Global
        right = str(right)
        ret = list()
        if right == 'VIEW':
            ret.append((self, 'MODERATE'))
        if right == 'ATTRIBUTE_READ':
            ret.append((self, 'VIEW'))
        if right == 'ATTRIBUTE_WRITE':
            ret.append((self, 'EDIT'))
        if right == 'MODERATE':
            ret.append((self, 'EDIT'))
        if right == 'EDIT':
            ret.append((self, 'MANAGE'))
        if right == 'MANAGE_PRIVILEGES':
            ret.append((Global.get_instance(), 'MANAGE_PRIVILEGES'))
            ret.append((self, 'MANAGE'))
        if right != 'ADMIN':
            ret.append((self, 'ADMIN'))
        if right == 'ADMIN':
            ret.append((Global.get_instance(), 'ADMIN'))

        return ret

    class ExportMeta(object):
        fields = [('id', 'VIEW')]

class EntityEvents(Events):
    model = Entity
    on_insert = on_update = on_delete = []

