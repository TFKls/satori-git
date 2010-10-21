# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models
from satori.dbev import Events
from satori.core.models import Role

class Contestant(Role):
    """Model. A Role for a contest participant.
    """
    __module__ = "satori.core.models"
    parent_role = models.OneToOneField(Role, parent_link=True, related_name='cast_contestant')

    contest    = models.ForeignKey('Contest')
    accepted   = models.BooleanField(default=False)
    invisible  = models.BooleanField(default=False)


    def inherit_right(self, right):
        right = str(right)
        ret = super(Contestant,self).inherit_right(right)
        ret.append((self.contest,right))
        return ret

class ContestantEvents(Events):
    model = Contestant
    on_insert = on_update = ['name', 'contest']
    on_delete = []

#! module api

from satori.objects import Argument, ReturnValue
from satori.ars.wrapper import WrapperClass, TypedList
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Contestant,User,Role,RoleMapping
from satori.core.sec import Token

class ApiContestant(WrapperClass):
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

