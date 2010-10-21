# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models
from satori.dbev import Events
from satori.core.models import Entity
from satori.core.models import Role
from satori.core.models import AttributeGroup

class Global(Entity):
    """Model. Special Global object for privileges.
    """
    __module__ = "satori.core.models"

    guardian = models.IntegerField(unique=True)

    anonymous = models.ForeignKey('Role', related_name='global_anonymous+')
    authenticated = models.ForeignKey('Role', related_name='global_authenticated+')
    checkers  = models.OneToOneField('AttributeGroup', related_name='group_global_checkers')
    generators = models.OneToOneField('AttributeGroup', related_name='group_global_generators')

    def save(self):
        self.guardian = 1

        try:
            x = self.checkers
        except AttributeGroup.DoesNotExist:
            checkers = AttributeGroup()
            checkers.save()
            self.checkers = checkers

        try:
            x = self.generators
        except AttributeGroup.DoesNotExist:
            generators = AttributeGroup()
            generators.save()
            self.generators = generators

        try:
            x = self.authenticated
        except Role.DoesNotExist:
            authenticated = Role(name='AUTHENTICATED', absorbing=False)
            authenticated.save()
            self.authenticated = authenticated

        try:
            x = self.anonymous
        except Role.DoesNotExist:
            anonymous = Role(name='ANONYMOUS', absorbing=False)
            anonymous.save()
            self.anonymous = anonymous

        super(Global, self).save()

    @staticmethod
    def get_instance():
        try:
            g = Global.objects.get(guardian=1)
        except:
            g = Global()
            g.save()
        return g

class GlobalEvents(Events):
    model = Global
    on_insert = on_update = on_delete = []
#! module api

from satori.ars.wrapper import TypedMap, WrapperClass
from satori.objects import Argument, ReturnValue
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Global
from satori.core.sec import Token
from satori.core.checking.accumulators import accumulators
from satori.core.checking.dispatchers import dispatchers

class ApiGlobal(WrapperClass):
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

