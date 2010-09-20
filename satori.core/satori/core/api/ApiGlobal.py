# vim:ts=4:sts=4:sw=4:expandtab

from satori.objects import Argument, ReturnValue
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Global
from satori.core.sec import Token

global_ = ModelWrapper(Global)

global_.attributes('checkers')
global_.attributes('generators')

@global_.method
@Argument('token', type=Token)
@ReturnValue(type=Global)
def get_instance(token):
    return Global.get_instance()

global_._fill_module(__name__)

