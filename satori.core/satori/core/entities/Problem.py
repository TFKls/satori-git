# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class Problem(Entity):
    """Model. Description of an (abstract) problems.
    """
    parent_entity     = models.OneToOneField(Entity, parent_link=True, related_name='cast_problem')

    name              = models.CharField(max_length=64, unique=True)
    description       = models.TextField(blank=True, default="")
    statement         = models.TextField(blank=True, default="")
    submit_fields     = models.TextField(blank=True, default="")

    default_test_data = AttributeGroupField(PCArg('self', 'VIEW'), PCArg('self', 'MANAGE'), '')

    class ExportMeta(object):
        fields = [('name', 'VIEW'), ('description', 'VIEW'), ('statement', 'VIEW'), ('submit_fields', 'VIEW')]

    def save(self, *args, **kwargs):
        self.fixup_default_test_data()
        super(Problem, self).save(*args, **kwargs)

    def __str__(self):
        return self.name+" ("+self.description+")"

    @ExportMethod(DjangoStruct('Problem'), [DjangoStruct('Problem')], PCGlobal('MANAGE_PROBLEMS'), [CannotSetField])
    @staticmethod
    def create(fields):
        problem = Problem()
        problem.forbid_fields(fields, ['id'])
        problem.update_fields(fields, ['name', 'description', 'statement', 'submit_fields'])
        problem.save()
        Privilege.grant(token_container.token.role, problem, 'MANAGE')
        return problem

    @ExportMethod(DjangoStruct('Problem'), [DjangoId('Problem'), DjangoStruct('Problem')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, ['id'])
        self.update_fields(fields, ['name', 'description', 'statement', 'submit_fields'])
        self.save()
        return self

    @ExportMethod(NoneType, [DjangoId('Problem')], PCArg('self', 'MANAGE'), [CannotDeleteObject])
    def delete(self):
        try:
            # should be done with cascading, but currently will not work
            for pm in self.problem_mappings.all():
                pm.delete()
            for ts in self.test_suites.all():
                ts.delete()
            for t in self.tests.all():
                t.delete()

            super(Problem, self).delete()
        except models.ProtectedError as e:
            raise CannotDeleteObject()

class ProblemEvents(Events):
    model = Problem
    on_insert = on_update = ['name']
    on_delete = []
