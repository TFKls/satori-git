from django.db import models
from satori.dbev import events
from satori.ars import django_
from satori.core.models._Object import Object
from satori.core.models._Message import Message

class MessageContest(Message):
    """Model. Description of a text message - contest msg.
    """
    __module__ = "satori.core.models"
    
    contest = models.ForeignKey('Contest')
    
    def __unicode__(self):
        return self.topic+" ("+self.contest.name+")"

