# vim:ts=4:sts=4:sw=4:expandtab

from satori.core.cwrapper import ModelWrapper
from satori.core.models import Message

message = ModelWrapper(Message)

message._fill_module(__name__)

