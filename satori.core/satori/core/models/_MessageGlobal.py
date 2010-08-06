# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._Message import Message

class MessageGlobal(Message):
    """Model. Description of a text message - main screen msg.
    """
    __module__ = "satori.core.models"
    parent_message = models.OneToOneField(Message, parent_link=True, related_name='cast_messageglobal')

    mainscreenonly = models.BooleanField()
    
    def __str__(self):
        return self.topic+" (Global)"

class MessageGlobalEvents(events.Events):
    model = MessageGlobal
    on_insert = on_update = ['topic', 'time']
    on_delete = []

