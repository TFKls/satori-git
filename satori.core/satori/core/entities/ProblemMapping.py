# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models

from satori.core.export        import ExportMethod
from satori.core.export_django import ExportModel, generate_attribute_group
from satori.dbev               import Events

from satori.core.models import Entity

@ExportModel
class ProblemMapping(Entity):
    """Model. Intermediary for many-to-many relationship between Contests and
    Problems.
    """

    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_problemmapping')

    contest     = models.ForeignKey('Contest')
    problem     = models.ForeignKey('Problem')
    code        = models.CharField(max_length=10)
    title       = models.CharField(max_length=64)
    default_test_suite = models.ForeignKey('TestSuite')

    generate_attribute_group('ProblemMapping', 'statement', 'VIEW', 'EDIT', globals(), locals())

    class ExportMeta(object):
        fields = [('contest', 'VIEW'), ('problem', 'VIEW'), ('code', 'VIEW'), ('title', 'VIEW'), ('default_test_suite', 'VIEW')]

    def save(self):
        self.fixup_statement()
        super(ProblemMapping, self).save()

    def __str__(self):
        return self.code+": "+self.title+ " ("+self.contest.name+","+self.problem.name+")"

    def inherit_right(self, right):
        right = str(right)
        ret = super(ProblemMapping, self).inherit_right(right)
        if right == 'VIEW':
            ret.append((self.contest,'VIEWTASKS'))
        if right == 'EDIT':
            ret.append((self.contest,'MANAGE'))
        if right == 'SUBMIT':
            ret.append((self.contest,'SUBMIT'))
        return ret


    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'code'), ('contest', 'problem'))

class ProblemMappingEvents(Events):
    model = ProblemMapping
    on_insert = on_update = ['contest', 'problem']
    on_delete = []

