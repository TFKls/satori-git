# vim:ts=4:sts=4:sw=4:expandtab

from satori.objects import Argument,ReturnValue
from satori.ars.wrapper import TypedList
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Contestant,User,Role,RoleMapping
from satori.core.sec import Token

contestant = ModelWrapper(Contestant)


@contestant.method
@Argument('token', type=Token)
@Argument('self', type=Contestant)
@ReturnValue(type=TypedList(User))
def members(token, self):
    result = list()
    for r in RoleMapping.objects.filter(parent = self, child__model = 'core.user'):
        result.append(r.child.cast_user)
    return result

#TODO: members.can method (rights needed?)

@contestant.method
@Argument('token', type=Token)
@Argument('self', type=Contestant)
@ReturnValue(type=str)
def name_auto(token,self):
    ret = ""
    for s in Contestant_members(token,self):
        if ret!="":
            ret = ret+","
        ret = ret+s.fullname
    return ret
    
contestant._fill_module(__name__)
