# vim:ts=4:sts=4:sw=4:expandtab

from satori.objects import Argument, ReturnValue
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Entity
from satori.core.sec import Token

object = ModelWrapper(Entity)

@object.method
@Argument('token', type=Token)
@Argument('self', type=Entity)
@Argument('right', type=str)
@ReturnValue(type=bool)
def demand_right(token, self, right):
    return self.demand_right(token, right)

object.attributes()

object._fill_module(__name__)

