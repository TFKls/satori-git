# vim:ts=4:sts=4:sw=4:expandtab
"""
Security and authorization procedures.
"""
from satori.sec.tools import CheckRights, RoleSet, Token, authenticateByLogin, authenticateByOpenIdStart, authenticateByOpenIdFinish
from satori.sec.store import Store

from satori.objects import DispatchOn, Argument
from satori.ars.model import NamedTuple, Contract, Procedure, Parameter, TypeAlias, Void, Boolean, Int32, Int64, String, NamedObject, Structure, ListType, SetType, MapType, Field, Argument
from satori.ars.naming import Name, ClassName, MethodName, FieldName, AccessorName, ParameterName, NamingStyle

contract_list = NamedTuple()

@DispatchOn(where = NamedTuple)
@Argument('name', type=Name)
@Argument('type', type=type)
def findByName(where, name, type):
    for item in where.items:
    	needle = findByName(item, name, type)
        if needle:
        	return needle
    return None
@DispatchOn(where = NamedObject)
@Argument('name', type=Name)
@Argument('type', type=type)
def findByName(where, name, type):
    if where.name == name and isinstance(where, type):
    	return where
    return None
@DispatchOn(where = TypeAlias)
@Argument('name', type=Name)
@Argument('type', type=type)
def findByName(where, name, type):
    if where.name == name and isinstance(where, type):
    	return where
    return findByName(where.target_type, name, type)
@DispatchOn(where = ListType)
@Argument('name', type=Name)
@Argument('type', type=type)
def findByName(where, name, type):
    if where.name == name and isinstance(where, type):
    	return where
    return findByName(where.element_type, name, type)
@DispatchOn(where = SetType)
@Argument('name', type=Name)
@Argument('type', type=type)
def findByName(where, name, type):
    if where.name == name and isinstance(where, type):
    	return where
    return findByName(where.element_type, name, type)
@DispatchOn(where = MapType)
@Argument('name', type=Name)
@Argument('type', type=type)
def findByName(where, name, type):
    if where.name == name and isinstance(where, type):
    	return where
    needle = findByName(where.key_type, name, type)
    if needle:
    	return needle
    return findByName(where.value_type, name, type)
@DispatchOn(where = Field)
@Argument('name', type=Name)
@Argument('type', type=type)
def findByName(where, name, type):
    return findByName(where.type, name, type)
@DispatchOn(where = Structure)
@Argument('name', type=Name)
@Argument('type', type=type)
def findByName(where, name, type):
    if where.name == name and isinstance(where, type):
    	return where
    for field in where.fields:
    	needle = findByName(field, name, type)
        if needle:
        	return needle
    return None
@DispatchOn(where = Parameter)
@Argument('name', type=Name)
@Argument('type', type=type)
def findByName(where, name, type):
    return findByName(where.type, name, type)
@DispatchOn(where = Procedure)
@Argument('name', type=Name)
@Argument('type', type=type)
def findByName(where, name, type):
    if where.name == name and isinstance(where, type):
    	return where
    for parameter in where.parameters:
    	needle = findByName(parameter, name, type)
        if needle:
        	return needle
    needle = findByName(where.return_type, name, type)
    if needle:
        return needle
    return findByName(where.error_type, name, type)
@DispatchOn(where = Contract)
@Argument('name', type=Name)
@Argument('type', type=type)
def findByName(where, name, type):
    if where.name == name and isinstance(where, type):
    	return where
    for procedure in where.procedures:
    	needle = findByName(procedure, name, type)
        if needle:
        	return needle
    return None





def generate_contract(contracts):
    contract = Contract(name=Name(ClassName('security')))
    userId = findByName(contracts, Name(ClassName('User'+'Id')), TypeAlias)
    objectId = findByName(contracts, Name(ClassName('Object'+'Id')), TypeAlias)

    whoami = Procedure(name=contract.name + Name(MethodName('whoAmI')), return_type=userId)
    whoami.addParameter(name=Name(ParameterName('token')), type=String)
    def whoami_impl(token):
        return int(Token(str(token)).user)
    whoami.implementation = whoami_impl
    contract.addProcedure(whoami)

    cani = Procedure(name=contract.name + Name(MethodName('canI')), return_type=Boolean)
    cani.addParameter(name=Name(ParameterName('token')), type=String)
    cani.addParameter(name=Name(ParameterName('object')), type=objectId)
    cani.addParameter(name=Name(ParameterName('right')), type=String)
    def cani_impl(token, object, right):
        checker = CheckRights()
        object = modelObject.objects.get(id=object)
        roleset = Roleset(user=User.objects.get(id=Token(token).user))
        return checker.check(roleset, object, right)
    cani.implementation = cani_impl
    contract.addProcedure(cani)

    login = Procedure(name=contract.name + Name(MethodName('login')), return_type=String)
    login.addParameter(name=Name(ParameterName('login')), type=String)
    login.addParameter(name=Name(ParameterName('password')), type=String)
    login.implementation = authenticateByLogin
    contract.addProcedure(login)

    openid_res = Structure(name=Name(ClassName('OpenIdResult')))
    openid_res.addField(name=Name(FieldName('token')), type=String)
    openid_res.addField(name=Name(FieldName('redirect')), type=String, optional=True)
    openid_res.addField(name=Name(FieldName('html')), type=String, optional=True)
    openid_start = Procedure(name=contract.name + Name(MethodName('openIdStart')), return_type=openid_res)
    openid_start.addParameter(name=Name(ParameterName('openid')), type=String)
    openid_start.addParameter(name=Name(ParameterName('realm')), type=String)
    openid_start.addParameter(name=Name(ParameterName('return_to')), type=String)
    openid_start.implementation = authenticateByOpenIdStart
    contract.addProcedure(openid_start)
    openid_finish = Procedure(name=contract.name + Name(MethodName('openIdFinish')), return_type=String)
    openid_finish.addParameter(name=Name(ParameterName('token')), type=String)
    openid_finish.addParameter(name=Name(ParameterName('args')), type=MapType(key_type=String, value_type=String))
    openid_finish.addParameter(name=Name(ParameterName('return_to')), type=String)
    openid_finish.implementation = authenticateByOpenIdFinish
    contract.addProcedure(openid_finish)

    return contract

def generate_contracts(contracts):
    contract_list.add(generate_contract(contracts))


