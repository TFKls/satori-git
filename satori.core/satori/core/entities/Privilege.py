# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models
from satori.dbev import Events
from satori.core.models import Entity
from satori.core.models import Global

class Privilege(Entity):
    """Model. Represents single right on object granted to the role.
    """
    __module__    = "satori.core.models"
    parent_object = models.OneToOneField(Entity, parent_link=True, related_name='cast_privilege')

    role     = models.ForeignKey('Role', related_name='privileges')
    object   = models.ForeignKey('Entity', related_name='privileged')
    right    = models.CharField(max_length=64)
    start_on  = models.DateTimeField(null=True)
    finish_on = models.DateTimeField(null=True)

    #class Meta:                                                # pylint: disable-msg=C0111
    #    unique_together = (('role', 'object', 'right'),)

    @staticmethod
    def grant(role, object, right, start_on=None, finish_on=None):
        (priv, created) = Privilege.objects.get_or_create(role=role, object=object, right=right)
        priv.start_on = start_on
        priv.finish_on = finish_on
        priv.save()

    @staticmethod
    def revoke(role, object, right):
        try:
            priv = Privilege.objects.get(role=role, object=object, right=right)
            priv.delete()
        except:
            pass

    @staticmethod
    def global_grant(role, right, start_on=None, finish_on=None):
        Privilege.grant(role, Global.get_instance(), right, start_on, finish_on)

    @staticmethod
    def global_revoke(role, right):
        Privilege.global_revoke(role, Global.get_instance(), right)


class PrivilegeEvents(Events):
    model = Privilege
    on_insert = on_update = ['role', 'object', 'right']
    on_delete = []

#! module api

from datetime import datetime
from types import NoneType

from satori.ars.wrapper import WrapperClass
from satori.objects import Argument, ReturnValue, Namespace
from satori.core.cwrapper import ModelWrapper, Struct
from satori.core.models import Privilege, Role, Global, Entity
from satori.core.sec import Token

PrivilegeTimes = Struct('PrivilegeTimes', (
    ('start_on', datetime, True),
    ('finish_on', datetime, True),
))

class ApiPrivilege(WrapperClass):
    privilege = ModelWrapper(Privilege)

    @privilege.method
    @Argument('token', type=Token)
    @Argument('role', type=Role)
    @Argument('object', type=Entity)
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
    @Argument('object', type=Entity)
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
    @Argument('object', type=Entity)
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
    def global_get(token, role, right):
        try:
            priv = Privilege.objects.get(role=role, object=Global.get_instance(), right=right)
            return Namespace(start_on=priv.start_on, finish_on=priv.finish_on)
        except Privilege.DoesNotExist:
            return None

    @privilege.global_get.can
    def global_get_can(token, role, right):
        return Global.get_instance().demand_right(token, 'MANAGE_PRIVILEGES')


