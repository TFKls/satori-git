# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import Events
from satori.core.models._Object import Object

class Subpage(Object):
    """Model. Subpage of a contest.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_subpage')
    contest = models.ForeignKey('Contest')
    public = models.BooleanField(default=True)
    name = models.TextField(blank=False)
    content = models.TextField()
    order = models.IntegerField()
    
    def inherit_right(self, right):
        right = str(right)
        ret = super(Subpage, self).inherit_right(right)
        if right=='VIEW':
            if public:
                ret.append((self.contest,'VIEW'))
        if right=='EDIT':
            ret.append((self.contest,'MANAGE'))
        return ret

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'name'),)


class SubpageEvents(Events):
    model = Subpage
    on_insert = on_update = []
    on_delete = []

