# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import Events
from satori.core.models._Object import Object
from satori.core.models._Role import Role
from satori.core.models._AttributeGroup import AttributeGroup

class Global(Object):
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
