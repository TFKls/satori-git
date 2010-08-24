# vim:ts=4:sts=4:sw=4:expandtab

from satori.core.cwrapper import ModelWrapper
from satori.core.models import Object

object = ModelWrapper(Object)

object._fill_module(__name__)

@object.method
@Argument('token',type=Token)
@Argument('self',type=Object)
@Argument('right',type=str)
@ReturnValue(type=bool)
def demand_right(token,self,right):
    return self.demand_right(str)
