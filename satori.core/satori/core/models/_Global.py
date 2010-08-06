# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._Object import Object

class Global(Object):
    """Model. Special Global object for privileges.
    """
    __module__ = "satori.core.models"

    guardian = models.IntegerField(unique=True)

    def save(self, *args, **kwargs):
        self.guardian = 1
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
        	ret.append(self, 'ADMIN')
        return ret

class GlobalEvents(events.Events):
    model = Global
    on_insert = on_update = on_delete = []
