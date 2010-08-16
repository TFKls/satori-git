# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._Object import Object

class AttributeGroup(Object):
    """
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_attribute_group')


class AttributeGroupEvents(events.Events):
    model = AttributeGroup
    on_insert = on_update = on_delete = []

