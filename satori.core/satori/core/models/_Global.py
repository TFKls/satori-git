# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._Object import Object
from satori.core.models._Role import Role

class Global(Object):
    """Model. Special Global object for privileges.
    """
    __module__ = "satori.core.models"

    guardian = models.IntegerField(unique=True)

    anonymous = models.ForeignKey('Role', related_name='global_anonymous+')
    authenticated = models.ForeignKey('Role', related_name='global_authenticated+')

    def save(self, *args, **kwargs):
        self.guardian = 1
        anonymous = Role(name='ANONYMOUS', absorbing=False)
        anonymous.save()
        self.anonymous = anonymous
        authenticated = Role(name='AUTHENTICATED', absorbing=False)
        authenticated.save()
        self.authenticated = authenticated
        super(Global, self).save(*args, **kwargs)

    @staticmethod
    def get_instance():
        try:
            g = Global.objects.get(guardian=1)
        except:
            g = Global()
            g.save()
        return g

    def inherit_right(self, right):
        right = str(right)
        ret = list()
        if right != 'ADMIN':
        	ret.append((self, 'ADMIN'))
        return ret

class GlobalEvents(events.Events):
    model = Global
    on_insert = on_update = on_delete = []
