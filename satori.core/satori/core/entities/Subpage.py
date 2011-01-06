# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class Subpage(Entity):
    """Model. Subpage or announcement. Can be tied to a contest.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_subpage')
    
    contest       = models.ForeignKey('Contest', related_name='subpages', null=True)
    is_public     = models.BooleanField(default=True)
    is_everywhere = models.BooleanField(default=False)
    is_announcement = models.BooleanField(default=False)
    name          = models.TextField(blank=False)
    content       = models.TextField()
    order         = models.IntegerField(null=True)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'name'),)
        ordering        = ('order',)

    class ExportMeta(object):
        fields = [('contest', 'VIEW'), ('is_public', 'VIEW'), ('is_everywhere', 'VIEW'), ('is_announcement', 'VIEW'), ('name', 'VIEW'), ('content', 'VIEW'), ('order', 'VIEW')]

    @classmethod
    def inherit_rights(cls):
        inherits = super(Subpage, cls).inherit_rights()
        cls._inherit_add(inherits, 'VIEW', 'contest', 'VIEW')
        cls._inherit_add(inherits, 'EDIT', 'contest', 'MANAGE')
        # TODO: conditional inherit: if contest is set and is_public, inherit VIEW from contest
        return inherits

    @ExportMethod(DjangoStruct('Subpage'), [unicode, unicode, bool, bool, int], PCGlobal('ADMIN'))
    @staticmethod
    def create_global_subpage(name, content, is_announcement, is_everywhere, order=0):
        subpage = Subpage()
        subpage.name = name
        subpage.content = content
        subpage.is_announcement = is_announcement
        subpage.is_everywhere = is_everywhere
        subpage.order = order
        subpage.save()
        return subpage

    @ExportMethod(DjangoStruct('Subpage'), [DjangoId('Contest'), unicode, unicode, bool, bool, int], PCArg('contest', 'MANAGE'))
    @staticmethod
    def create_contest_subpage(contest, name, content, is_announcement, is_public, order=0):
        subpage = Subpage()
        subpage.contest = contest
        subpage.name = name
        subpage.content = content
        subpage.is_announcement = is_announcement
        subpage.is_public = is_public
        subpage.order = order
        subpage.save()
        return subpage

    @ExportMethod(DjangoStructList('Subpage'), [boolean], PCPermit())
    @staticmethod
    def get_global_subpages(announcements):
        return Subpage.objects.filter(is_announcement=announcements, contest=None)

    @ExportMethod(DjangoStructList('Subpage'), [DjangoId('Contest'), boolean], PCPermit())
    @staticmethod
    def get_contest_subpages(contest, announcements):
        return Subpage.objects.filter(is_announcement=announcements, contest=contest) | Subpage.objects.filter(is_announcement=announcements, contest=None, is_everywhere=True)

class SubpageEvents(Events):
    model = Subpage
    on_insert = on_update = []
    on_delete = []
