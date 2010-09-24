# vim:ts=4:sts=4:sw=4:expandtab

from datetime import datetime
from types import NoneType

from satori.objects import Argument, ReturnValue
from satori.core.cwrapper import ModelWrapper, Struct
from satori.core.models import Privilege, Role, Global, Object
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

PrivilegeTimes = Struct('PrivilegeTimes', (
    ('start_on', datetime, True),
    ('finish_on', datetime, True),
))

@privilege.method
@Argument('token', type=Token)
@Argument('role', type=Role)
@Argument('object', type=Object)
@Argument('right', type=basestring)
@Argument('start_on', type=(datetime, NoneType))
@Argument('finish_on', type=(datetime, NoneType))
@ReturnValue(type=NoneType)
def grant(token, role, object, right, start_on=None, finish_on=None):
    Privilege.grant(role, object, right, start_on, finish_on)

@privilege.grant.can
def grant_can(token, role, object, right, start_on=None, finish_on=None):
    return object.demand_right(token, 'MANAGE_PRIVILEGES')

@privilege.method
@Argument('token', type=Token)
@Argument('role', type=Role)
@Argument('object', type=Object)
@Argument('right', type=basestring)
@ReturnValue(type=NoneType)
def revoke(token, role, object, right):
    Privilege.revoke(role, object, right)

@privilege.revoke.can
def revoke_can(token, role, object, right):
    return object.demand_right(token, 'MANAGE_PRIVILEGES')

@privilege.method
@Argument('token', type=Token)
@Argument('role', type=Role)
@Argument('object', type=Object)
@Argument('right', type=basestring)
@ReturnValue(type=PrivilegeTimes)
def get(token, role, object, right):
    try:
        priv = Privilege.objects.get(role=role, object=object, right=right)
        return Namespace(start_on=priv.start_on, finish_on=priv.finish_on)
    except Privilege.DoesNotExist:
        return None

@privilege.get.can
def get_can(token, role, object, right):
    return object.demand_right(token, 'MANAGE_PRIVILEGES')

@privilege.method
@Argument('token', type=Token)
@Argument('role', type=Role)
@Argument('right', type=basestring)
@Argument('start_on', type=(datetime, NoneType))
@Argument('finish_on', type=(datetime, NoneType))
@ReturnValue(type=NoneType)
def global_grant(token, role, right, start_on=None, finish_on=None):
    Privilege.global_grant(role, right, start_on, finish_on)

@privilege.global_grant.can
def global_grant_can(token, role, right, start_on=None, finish_on=None):
    return Global.get_instance().demand_right(token, 'MANAGE_PRIVILEGES')

@privilege.method
@Argument('token', type=Token)
@Argument('role', type=Role)
@Argument('right', type=basestring)
@ReturnValue(type=NoneType)
def global_revoke(token, role, right):
    Privilege.global_revoke(role, right)

@privilege.global_revoke.can
def global_revoke_can(token, role, right):
    return Global.get_instance().demand_right(token, 'MANAGE_PRIVILEGES')

@privilege.method
@Argument('token', type=Token)
@Argument('role', type=Role)
@Argument('right', type=basestring)
@ReturnValue(type=PrivilegeTimes)
def get(token, role, right):
    try:
        priv = Privilege.objects.get(role=role, object=Global.get_instance(), right=right)
        return Namespace(start_on=priv.start_on, finish_on=priv.finish_on)
    except Privilege.DoesNotExist:
        return None

@privilege.get.can
def get_can(token, role, right):
    return Global.get_instance().demand_right(token, 'MANAGE_PRIVILEGES')

privilege._fill_module(__name__)

