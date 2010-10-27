# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models

from satori.core.export        import ExportMethod
from satori.core.export_django import ExportModel
from satori.dbev               import Events

from satori.core.models import Entity

@ExportModel
class Subpage(Entity):
    """Model. Subpage of a contest.
    """
    
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_subpage')
    
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

    class ExportMeta(object):
        fields = [('contest', 'VIEW'), ('public', 'VIEW'), ('name', 'VIEW'), ('content', 'VIEW'), ('order', 'VIEW')]


class SubpageEvents(Events):
    model = Subpage
    on_insert = on_update = []
    on_delete = []

