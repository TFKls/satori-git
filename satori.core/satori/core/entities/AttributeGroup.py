# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

class AttributeGroup(Entity):
    """Model. Open attribute group.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_attribute_group')

class AttributeGroupEvents(Events):
    model = AttributeGroup
    on_insert = on_update = on_delete = []
