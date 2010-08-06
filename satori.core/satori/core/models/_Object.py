# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events

class Object(models.Model):
    """Model. Base for all database objects. Provides common GUID space.
    """
    __module__ = "satori.core.models"

    model = models.CharField(max_length=64, editable=False)

    def save(self, *args, **kwargs):
        if not self.model:
        	  self.model = self._meta.app_label + '.' + self._meta.object_name
        super(Object, self).save(*args, **kwargs)
    
    @classmethod
    def ars_type(cls):
        if not '_ars_type' in cls.__dict__:
            from satori.core import cwrapper
        	cls._ars_type = cwrapper.DjangoTypeAlias(cls)

        return cls._ars_type

    def inherit_right(self, right):
        right = str(right)
        ret = list()
        if right == 'VIEW':
        	ret.append((self,'MODERATE'))
        if right == 'MODERATE':
        	ret.append((self,'EDIT'))
        if right != 'ADMIN':
        	  ret.append((self,'ADMIN'))
        return ret
    
    def demand_right(self, token, right):
        from satori.core.sec import Token, RoleSet, RightCheck
        checker = RightCheck()
        roleset = RoleSet(token=Token)
        return checker(roleset, self, str(right))
        if not cani:
        	raise 'Insufficient rights'

class ObjectEvents(events.Events):
    model = Object
    on_insert = on_update = on_delete = []
