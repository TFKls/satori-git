# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class Message(Entity):
    """Model. Description of a text message.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_message')

    topic         = models.CharField(max_length=50, unique=True)
    content       = models.TextField(blank=True, default="")
    time          = models.DateTimeField(auto_now_add=True)

    class ExportMeta(object):
        fields = [('topic', 'VIEW'), ('content', 'VIEW'), ('time', 'VIEW')]

    def __str__(self):
        return self.topic

class MessageEvents(Events):
    model = Message
    on_insert = on_update = ['topic', 'time']
    on_delete = []
