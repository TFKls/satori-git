# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models

from satori.core.export        import ExportMethod
from satori.core.export_django import ExportModel
from satori.core.dbev               import Events

from satori.core.models import Message

@ExportModel
class MessageContest(Message):
    """Model. Description of a text message - contest msg.
    """
    __module__ = "satori.core.models"
    parent_message = models.OneToOneField(Message, parent_link=True, related_name='cast_messagecontest')

    contest = models.ForeignKey('Contest')

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

