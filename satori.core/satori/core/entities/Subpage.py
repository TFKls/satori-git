# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models
from satori.dbev import Events
from satori.core.models import Entity
from satori.core.models import Global

class Subpage(Entity):
    """Model. Subpage of a contest.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Entity, parent_link=True, related_name='cast_subpage')
    contest = models.ForeignKey('Contest')
    public = models.BooleanField(default=True)
    name = models.TextField(blank=False)
    content = models.TextField()
    order = models.IntegerField(null=True)

    def inherit_right(self, right):
        right = str(right)
        ret = super(Subpage, self).inherit_right(right)
        if right=='VIEW':
            ret.append((self.contest,'VIEW'))
            if self.public:
                ret.append((Global.get_instance().authenticated,'VIEW_BASICS'))
        if right=='EDIT':
            ret.append((self.contest,'MANAGE'))
        return ret

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'name'),)


class SubpageEvents(Events):
    model = Subpage
    on_insert = on_update = []
    on_delete = []

#! module api

from satori.ars.wrapper import WrapperClass
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Subpage

class ApiSubpage(WrapperClass):
    subpage = ModelWrapper(Subpage)

