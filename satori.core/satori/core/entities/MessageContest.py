# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Message

@ExportModel
class MessageContest(Message):
    """Model. Description of a text message - contest msg.
    """
    parent_message = models.OneToOneField(Message, parent_link=True, related_name='cast_messagecontest')

    contest        = models.ForeignKey('Contest', related_name='messages')

    class ExportMeta(object):
        fields = [('contest', 'VIEW')]

    @classmethod
    def inherit_rights(cls):
        inherits = super(MessageContest, cls).inherit_rights()
        for key in inherits.keys():
            cls._inherit_add(inherits, key, 'contest', key)
        return inherits

class MessageContestEvents(Events):
    model = MessageContest
    on_insert = on_update = ['topic', 'time']
    on_delete = []
