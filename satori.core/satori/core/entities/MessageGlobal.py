# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models

from satori.core.export        import ExportMethod
from satori.core.export_django import ExportModel
from satori.core.dbev               import Events

from satori.core.models import Message

@ExportModel
class MessageGlobal(Message):
    """Model. Description of a text message - main screen msg.
    """
    __module__ = "satori.core.models"
    parent_message = models.OneToOneField(Message, parent_link=True, related_name='cast_messageglobal')

    mainscreenonly = models.BooleanField()

    class ExportMeta(object):
        fields = [('mainscreenonly', 'VIEW')]

    def __str__(self):
        return self.topic+" (Global)"

    @classmethod
    def inherit_rights(cls):
        inherits = super(MessageGlobal, cls).inherit_rights()
        for key in inherits.keys():
            cls._inherit_add(inherits, key, 'contest', key)
        cls._inherit_add(inherits, 'VIEW', '', 'VIEW_BASICS')
        return inherits

class MessageGlobalEvents(Events):
    model = MessageGlobal
    on_insert = on_update = ['topic', 'time']
    on_delete = []
