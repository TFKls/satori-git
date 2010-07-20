from django.db import models
from satori.dbev import events
from satori.ars import django_
from satori.core.models._Object import Object
from satori.core.models._Message import Message

class MessageContest(Message):
    """Model. Description of a text message - contest msg.
    """
    __module__ = "satori.core.models"
    parent_message = models.OneToOneField(Message, parent_link=True, related_name='cast_messagecontest')
    
    contest = models.ForeignKey('Contest')
    
    def __unicode__(self):
        return self.topic+" ("+self.contest.name+")"

class MessageContestEvents(events.Events):
    model = MessageContest
    on_insert = on_update = ['topic', 'time']
    on_delete = []

class MessageContestOpers(django_.Opers):
    messagecontest = django_.ModelProceduresProvider(MessageContest)

