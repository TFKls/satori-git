from django.db import models
from satori.dbev import events
from satori.ars import django_
from satori.core.models._Role import Role

class Contestant(Role):
    """Model. A Role for a contest participant.
    """
    __module__ = "satori.core.models"
    parent_role = models.OneToOneField(Role, parent_link=True, related_name='cast_contestant')

    contest    = models.ForeignKey('Contest')
    user       = models.ForeignKey('User')
    accepted   = models.BooleanField()
    def __unicode__(self):
        return self.user.fullname+' ('+self.contest.name+')'


class ContestantEvents(events.Events):
    model = Contestant
    on_insert = on_update = ['name', 'contest']
    on_delete = []

class ContestantOpers(django_.Opers):
    contestant = django_.ModelProceduresProvider(Contestant)

