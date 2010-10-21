# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models
from satori.dbev import Events

class Entity(models.Model):
    """Model. Base for all database objects. Provides common GUID space.
    """
    __module__ = "satori.core.models"

    model = models.CharField(max_length=64, editable=False)

    def save(self, *args, **kwargs):
        if not self.model:
              self.model = self._meta.app_label + '.' + self._meta.module_name
        super(Entity, self).save(*args, **kwargs)

    @classmethod
    def ars_type(cls):
        if not '_ars_type' in cls.__dict__:
            from satori.core.cwrapper import ArsDjangoModel
            cls._ars_type = ArsDjangoModel(cls)

        return cls._ars_type

    def inherit_right(self, right):
        from satori.core.models import Global
        right = str(right)
        ret = list()
        if right == 'VIEW':
            ret.append((self, 'MODERATE'))
        if right == 'ATTRIBUTE_READ':
            ret.append((self, 'VIEW'))
        if right == 'ATTRIBUTE_WRITE':
            ret.append((self, 'EDIT'))
        if right == 'MODERATE':
            ret.append((self, 'EDIT'))
        if right == 'EDIT':
            ret.append((self, 'MANAGE'))
        if right == 'MANAGE_PRIVILEGES':
            ret.append((Global.get_instance(), 'MANAGE_PRIVILEGES'))
            ret.append((self, 'MANAGE'))
        if right != 'ADMIN':
            ret.append((self, 'ADMIN'))
        if right == 'ADMIN':
            ret.append((Global.get_instance(), 'ADMIN'))

        return ret

    def demand_right(self, token, right):
        from satori.core.sec import Token, RoleSet, RightCheck
        checker = RightCheck()
        roleset = RoleSet(token=token)
        return checker(roleset, self, str(right))

class EntityEvents(Events):
    model = Entity
    on_insert = on_update = on_delete = []
#! module api

from satori.ars.wrapper import WrapperClass
from satori.objects import Argument, ReturnValue
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Entity
from satori.core.sec import Token

class ApiEntity(WrapperClass):
    object = ModelWrapper(Entity)

    @object.method
    @Argument('token', type=Token)
    @Argument('self', type=Entity)
    @Argument('right', type=str)
    @ReturnValue(type=bool)
    def demand_right(token, self, right):
        return self.demand_right(token, right)

    object.attributes()

