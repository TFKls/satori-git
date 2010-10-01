# vim:ts=4:sts=4:sw=4:expandtab

from satori.ars.wrapper import TypedMap
from satori.objects import Argument, ReturnValue
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Global
from satori.core.sec import Token
from satori.core.checking.accumulators import accumulators
from satori.core.checking.dispatchers import dispatchers

global_ = ModelWrapper(Global)

global_.attributes('checkers')
global_.attributes('generators')

@global_.method
@Argument('token', type=Token)
@ReturnValue(type=Global)
def get_instance(token):
    return Global.get_instance()

@global_.method
@Argument('token', type=Token)
@ReturnValue(type=TypedMap(unicode, unicode))
def get_accumulators(token):
    ret = {}
    for name in accumulators:
        ret[name] = accumulators[name].__doc__
        if ret[name] is None:
            ret[name] = ''
    return ret

@global_.method
@Argument('token', type=Token)
@ReturnValue(type=TypedMap(unicode, unicode))
def get_dispatchers(token):
    ret = {}
    for name in dispatchers:
        ret[name] = dispatchers[name].__doc__
        if ret[name] is None:
            ret[name] = ''
    return ret

global_._fill_module(__name__)

