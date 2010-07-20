from django.db import models
from satori.dbev import events
from satori.ars import django_
from satori.core.models._Object import Object

class Message(Object):
    """Model. Description of a text message.
    """
    __module__ = "satori.core.models"

    topic       = models.CharField(max_length=50, unique=True)
    content     = models.TextField(blank=True, default="")
    time        = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.topic

