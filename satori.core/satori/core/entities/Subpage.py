# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev               import Events

from satori.core.models import Entity

@ExportModel
class Subpage(Entity):
    """Model. Subpage of a contest.
    """
    
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_subpage')
    
    contest = models.ForeignKey('Contest')
    pub = models.BooleanField(default=True)
    name = models.TextField(blank=False)
    content = models.TextField()
    order = models.IntegerField(null=True)

    @classmethod
    def inherit_rights(cls):
        inherits = super(Subpage, cls).inherit_rights()
        cls._inherit_add(inherits, 'VIEW', 'contest', 'VIEW')
        cls._inherit_add(inherits, 'EDIT', 'contest', 'MANAGE')
        return inherits

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'name'),)

    class ExportMeta(object):
        fields = [('contest', 'VIEW'), ('pub', 'VIEW'), ('name', 'VIEW'), ('content', 'VIEW'), ('order', 'VIEW')]


class SubpageEvents(Events):
    model = Subpage
    on_insert = on_update = []
    on_delete = []

