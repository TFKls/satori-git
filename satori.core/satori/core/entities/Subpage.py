# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class Subpage(Entity):
    """Model. Subpage or announcement. Can be tied to a contest.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_subpage')
    
    contest       = models.ForeignKey('Contest', related_name='subpages', null=True, on_delete=models.CASCADE)
    is_public     = models.BooleanField(default=True)
    is_sticky     = models.BooleanField(default=False)
    is_announcement = models.BooleanField(default=False)
    name          = models.TextField(blank=False)
    order         = models.IntegerField(default=0)
    date_created  = models.DateTimeField(auto_now_add=True)
    
    content       = models.TextField()
    content_files = AttributeGroupField(PCArg('self', 'VIEW'), PCArg('self', 'MANAGE'), '')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'name'),)
        ordering        = ('order',)

    class ExportMeta(object):
        fields = [('contest', 'VIEW'), ('is_public', 'VIEW'), ('is_sticky', 'VIEW'), ('is_announcement', 'VIEW'), ('name', 'VIEW'), ('content', 'VIEW'), ('order', 'VIEW'), ('date_created', 'VIEW')]

    def save(self, *args, **kwargs):
        self.fixup_content_files()
        return super(Subpage, self).save(*args, **kwargs)

    @classmethod
    def inherit_rights(cls):
        inherits = super(Subpage, cls).inherit_rights()
        cls._inherit_add(inherits, 'VIEW', 'contest', 'VIEW', 'is_public', '1')
        cls._inherit_add(inherits, 'MANAGE', 'contest', 'MANAGE')
        # TODO: conditional inherit: if contest is set and is_public, inherit VIEW from contest
        return inherits

    @ExportMethod(DjangoStruct('Subpage'), [DjangoStruct('Subpage')], PCGlobal('ADMIN'), [CannotSetField, SphinxException])
    @staticmethod
    def create_global(fields):
        subpage = Subpage()
        subpage.forbid_fields(fields, ['id', 'contest'])
        subpage.update_fields(fields, ['name', 'content', 'is_announcement', 'is_sticky', 'is_public', 'order'])
        subpage.save()
        subpage.content_files_set_map(render_sphinx(subpage.content, subpage.content_files_get_map()))
        return subpage

    @ExportMethod(DjangoStruct('Subpage'), [DjangoStruct('Subpage')], PCArgField('fields', 'contest', 'MANAGE'), [CannotSetField, SphinxException])
    @staticmethod
    def create_for_contest(fields):
        subpage = Subpage()
        subpage.forbid_fields(fields, ['id'])
        subpage.update_fields(fields, ['name', 'contest', 'content', 'is_announcement', 'is_sticky', 'is_public', 'order'])
        subpage.save()
        subpage.content_files_set_map(render_sphinx(subpage.content, subpage.content_files_get_map()))
        return subpage

    @ExportMethod(DjangoStruct('Subpage'), [DjangoId('Subpage'), DjangoStruct('Subpage')], PCArg('self', 'MANAGE'), [CannotSetField, SphinxException])
    def modify(self, fields):
        self.forbid_fields(fields, ['id', 'contest'])
        self.update_fields(fields, ['name', 'content', 'is_announcement', 'is_sticky', 'is_public', 'order'])
        self.save()
        self.content_files_set_map(render_sphinx(self.content, self.content_files_get_map()))
        return self
        
    @ExportMethod(NoneType, [DjangoId('Subpage')], PCArg('self', 'MANAGE'), [CannotDeleteObject])
    def delete(self):
        try:
            super(Subpage, self).delete()
        except models.ProtectedError as e:
            raise CannotDeleteObject()

    @ExportMethod(DjangoStructList('Subpage'), [bool], PCPermit())
    @staticmethod
    def get_global(announcements):
        return Subpage.objects.filter(is_announcement=announcements, contest=None)

    @ExportMethod(DjangoStructList('Subpage'), [DjangoId('Contest'), bool], PCPermit())
    @staticmethod
    def get_for_contest(contest, announcements):
        return Subpage.objects.filter(is_announcement=announcements, contest=contest) | Subpage.objects.filter(is_announcement=announcements, contest=None, is_public=True)

class SubpageEvents(Events):
    model = Subpage
    on_insert = on_update = []
    on_delete = []
