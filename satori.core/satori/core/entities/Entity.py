# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models
from satori.core.dbev import Events
from satori.core.export import ExportMethod, PCPermit
from satori.core.export_django import ExportModel, DjangoId, generate_attribute_group

@ExportModel
class Entity(models.Model):
    """Model. Base for all database objects. Provides common GUID space.

    rights:
        VIEW
        MANAGE
        MANAGE_PRIVILEGES - do wywalenie, rownowazne z MANAGE
    """
    __module__ = "satori.core.models"

    model = models.CharField(max_length=64, editable=False)

    generate_attribute_group('Entity', None, 'MANAGE', 'MANAGE', globals(), locals())

    def save(self, *args, **kwargs):
        if not self.model:
              self.model = self._meta.app_label + '.' + self._meta.module_name
        super(Entity, self).save(*args, **kwargs)

    @classmethod
    def _inherit_add(cls, inherits, get, id, need):
        if get not in inherits:
        	inherits[get] = []
        inherits[get].append((id, need))

    @classmethod
    def inherit_rights(cls):
        inherits = dict()

        cls._inherit_add(inherits, 'VIEW', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'MANAGE', '', 'ADMIN')
        cls._inherit_add(inherits, 'MANAGE_PRIVILEGES', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'MANAGE_PRIVILEGES', '', 'MANAGE_PRIVILEGES')
        return inherits

    class ExportMeta(object):
        fields = [('id', 'VIEW')]

class EntityEvents(Events):
    model = Entity
    on_insert = on_update = on_delete = []

