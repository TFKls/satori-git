# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class ProblemMapping(Entity):
    """Model. Intermediary for many-to-many relationship between Contests and
    Problems.
    """
    parent_entity      = models.OneToOneField(Entity, parent_link=True, related_name='cast_problemmapping')

    contest            = models.ForeignKey('Contest', related_name='problem_mappings+')
    problem            = models.ForeignKey('Problem', related_name='problem_mappings+')
    code               = models.CharField(max_length=10)
    title              = models.CharField(max_length=64)
    default_test_suite = models.ForeignKey('TestSuite', related_name='problem_mappings+')

    statement          = AttributeGroupField(PCArg('self', 'VIEW'), PCArg('self', 'MANAGE'), '')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('contest', 'code'), ('contest', 'problem'))

    class ExportMeta(object):
        fields = [('contest', 'VIEW'), ('problem', 'MANAGE'), ('code', 'VIEW'), ('title', 'VIEW'), ('default_test_suite', 'MANAGE')]

    @classmethod
    def inherit_rights(cls):
        inherits = super(ProblemMapping, cls).inherit_rights()
        cls._inherit_add(inherits, 'VIEW', 'contest', 'VIEW_TASKS')
        cls._inherit_add(inherits, 'MANAGE', 'contest', 'MANAGE')
        cls._inherit_add(inherits, 'SUBMIT', 'contest', 'SUBMIT')
        return inherits

    def save(self, *args, **kwargs):
        self.fixup_statement()
        super(ProblemMapping, self).save(*args, **kwargs)

    def __str__(self):
        return self.code+": "+self.title+ " ("+self.contest.name+","+self.problem.name+")"

    @ExportMethod(DjangoStruct('ProblemMapping'), [DjangoStruct('ProblemMapping')], PCAnd(PCArgField('fields', 'contest', 'MANAGE'), PCArgField('fields', 'problem', 'MANAGE')), [CannotSetField])
    @staticmethod
    def create(fields):
        problem_mapping = ProblemMapping()
        problem_mapping.forbid_fields(fields, [ 'id' ])
        problem_mapping.update_fields(fields, [ 'contest', 'problem', 'code', 'title', 'default_test_suite' ])
        if problem_mapping.problem != problem_mapping.default_test_suite.problem:
            raise CannotSetField()
        problem_mapping.save()
        Privilege.grant(problem_mapping.contest.admin_role, problem_mapping.problem, 'MANAGE')
        return problem_mapping

    @ExportMethod(DjangoStruct('ProblemMapping'), [DjangoId('ProblemMapping'), DjangoStruct('ProblemMapping')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, [ 'id', 'contest', 'problem' ])
        update = self.update_fields(fields, [ 'code', 'title', 'default_test_suite' ])
        if self.problem != self.default_test_suite.problem:
            raise CannotSetField()
        self.save()
        if 'default_test_suite' in update:
            RawEvent().send(Event(type='checking_default_test_suite_change', id=self.id))
        return self

class ProblemMappingEvents(Events):
    model = ProblemMapping
    on_insert = on_update = ['contest', 'problem']
    on_delete = []
