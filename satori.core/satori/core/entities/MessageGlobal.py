# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models
from satori.dbev import Events
from satori.core.models import Message
from satori.core.models import Global

class MessageGlobal(Message):
    """Model. Description of a text message - main screen msg.
    """
    __module__ = "satori.core.models"
    parent_message = models.OneToOneField(Message, parent_link=True, related_name='cast_messageglobal')

    mainscreenonly = models.BooleanField()

    def __str__(self):
        return self.topic+" (Global)"

    def inherit_right(self, right):
        right = str(right)
        ret = super(MessageGlobal,self).inherit_right(right)
        if right=='VIEW':
            ret.append((Global.get_instance(),'VIEW_BASICS'))
        return ret

class MessageGlobalEvents(Events):
    model = MessageGlobal
    on_insert = on_update = ['topic', 'time']
    on_delete = []

#! module api

from satori.ars.wrapper import WrapperClass
from satori.core.cwrapper import ModelWrapper
from satori.core.models import MessageGlobal

class ApiMessageGlobal(WrapperClass):
    message_global = ModelWrapper(MessageGlobal)

