# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev import Events

@ExportModel
class Entity(models.Model):
    """Model. Base for all database objects. Provides common GUID space.

    rights:
        VIEW
        MANAGE
    """
    model = models.CharField(max_length=64, editable=False)
    oa    = DefaultAttributeGroupField(PCArg('self', 'MANAGE'), PCArg('self', 'MANAGE'), 'An attribute group to be used for general-purpose data.')

    class ExportMeta(object):
        fields = [('id', 'VIEW')]

    @classmethod
    def inherit_rights(cls):
        inherits = dict()
        cls._inherit_add(inherits, 'VIEW', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'MANAGE', '', 'ADMIN')
        return inherits

    def save(self, *args, **kwargs):
        if not self.model:
              self.model = self._meta.app_label + '.' + self._meta.module_name
        super(Entity, self).save(*args, **kwargs)

    @classmethod
    def _inherit_add(cls, inherits, get, id, need):
        if get not in inherits:
        	inherits[get] = []
        inherits[get].append((id, need))

class EntityEvents(Events):
    model = Entity
    on_insert = on_update = on_delete = []
