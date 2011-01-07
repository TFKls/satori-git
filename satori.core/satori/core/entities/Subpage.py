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
    date_created  = models.DateTimeField(auto_now_add=True)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'name'),)
        ordering        = ('order',)

    class ExportMeta(object):
        fields = [('contest', 'VIEW'), ('is_public', 'VIEW'), ('is_everywhere', 'VIEW'), ('is_announcement', 'VIEW'), ('name', 'VIEW'), ('content', 'VIEW'), ('order', 'VIEW'), ('date_created', 'VIEW')]

    @classmethod
    def inherit_rights(cls):
        inherits = super(Subpage, cls).inherit_rights()
        cls._inherit_add(inherits, 'VIEW', 'contest', 'VIEW')
        cls._inherit_add(inherits, 'EDIT', 'contest', 'MANAGE')
        # TODO: conditional inherit: if contest is set and is_public, inherit VIEW from contest
        return inherits

    @ExportMethod(DjangoStruct('Subpage'), [DjangoStruct('Test')], PCGlobal('ADMIN'))
    @staticmethod
    def create_global(fields)
        subpage = Subpage()
        subpage.name = fields.name
        subpage.content = fields.content
        subpage.is_announcement = fields.is_announcement
        subpage.is_everywhere = fields.is_everywhere
        subpage.order = fields.order
        subpage.save()
        return subpage

    @ExportMethod(DjangoStruct('Subpage'), [DjangoId('Contest'), unicode, unicode, bool, bool, int], PCArg('contest', 'MANAGE'))
    @ExportMethod(DjangoStruct('Subpage'), [DjangoStruct('Test')], PCArgField('fields', 'contest', 'MANAGE'))
    @staticmethod
    def create_for_contest(fields):
        subpage = Subpage()
        subpage.contest = fields.contest
        subpage.name = fields.name
        subpage.content = fields.content
        subpage.is_announcement = fields.is_announcement
        subpage.is_public = fields.is_public
        subpage.order = fields.order
        subpage.save()
        return subpage

    @ExportMethod(DjangoStruct('Subpage'), [DjangoId('Subpage'), DjangoStruct('Subpage')], PCArg('self', 'MANAGE'))
    def modify(self, fields):
        self.name = fields.name
        self.content = fields.content
        self.is_announcement = fields.is_announcement
        if self.contest is None:
            self.is_everywhere = fields.is_everywhere
        else:
            self.is_public = fields.is_public
        self.order = fields.order
        self.save()
        return self

    #@ExportMethod(NoneType, [DjangoId('Subpage')], PCArg('self', 'MANAGE'), [CannotDeleteObject])
    def delete(self):
        logging.error('subpage deleted') #TODO: Waiting for non-cascading deletes in django
        self.privileges.all().delete()
        try:
            super(Subpage, self).delete()
        except DatabaseError:
            raise CannotDeleteObject()

    @ExportMethod(DjangoStructList('Subpage'), [bool], PCPermit())
    @staticmethod
    def get_global(announcements):
        return Subpage.objects.filter(is_announcement=announcements, contest=None)

    @ExportMethod(DjangoStructList('Subpage'), [DjangoId('Contest'), bool], PCPermit())
    @staticmethod
    def get_for_contest(contest, announcements):
        return Subpage.objects.filter(is_announcement=announcements, contest=contest) | Subpage.objects.filter(is_announcement=announcements, contest=None, is_everywhere=True)

class SubpageEvents(Events):
    model = Subpage
    on_insert = on_update = []
    on_delete = []
