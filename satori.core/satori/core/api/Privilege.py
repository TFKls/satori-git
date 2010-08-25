# vim:ts=4:sts=4:sw=4:expandtab

from satori.objects import Argument, ReturnValue
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Privilege, Role, Global
from satori.core.sec import Token

privilege = ModelWrapper(Privilege)

@privilege.method
@Argument('token', type=Token)
@Argument('role', type=Role)
@Argument('right', type=str)
@ReturnValue(type=Privilege)
def create_global(token, role, right):
    globe = Global.get_instance()
    p = Privilege(role=role, object=globe, right=right)
    p.save()
    return p

@privilege.create_global.can
def create_global_check(token, role, right):
    return True
#TODO: FIX this!
	return Global.get_instance().demand_right('MANAGE_PRIVILEGES')

@privilege.create.can
def create_check(*args, **kwargs):
    return True
#TODO: FIX this!
	return object.demand_right(token, 'MANAGE_PRIVILEGES')

@privilege.delete.can
def delete_check(token, self):
    return self.object.demand_right(token, 'MANAGE_PRIVILEGES')

privilege._fill_module(__name__)

