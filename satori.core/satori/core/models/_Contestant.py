# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import Events
from satori.core.models._Role import Role

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

