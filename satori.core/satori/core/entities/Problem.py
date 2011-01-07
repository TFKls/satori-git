# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class Problem(Entity):
    """Model. Description of an (abstract) problems.
    """
    parent_entity     = models.OneToOneField(Entity, parent_link=True, related_name='cast_problem')

    name              = models.CharField(max_length=50, unique=True)
    description       = models.TextField(blank=True, default="")
    statement         = models.TextField(blank=True, default="")

    default_test_data = AttributeGroupField(PCArg('self', 'VIEW'), PCArg('self', 'MANAGE'), '')

    class ExportMeta(object):
        fields = [('name', 'VIEW'), ('description', 'VIEW'), ('statement', 'VIEW')]

    def save(self, *args, **kwargs):
        self.fixup_default_test_data()
        super(Problem, self).save(*args, **kwargs)

    def __str__(self):
        return self.name+" ("+self.description+")"

    @ExportMethod(DjangoStruct('Problem'), [DjangoStruct('Problem')], PCGlobal('MANAGE_PROBLEMS'))
    @staticmethod
    def create(fields):
        problem = Problem()
        problem.name = fields.name
        problem.description = fields.description
        problem.statement = fields.statement
        problem.save()
        Privilege.grant(token_container.token.role, problem, 'MANAGE')
        return problem

    @ExportMethod(DjangoStruct('Problem'), [DjangoId('Problem'), DjangoStruct('Problem')], PCArg('self', 'MANAGE'))
    def modify(self, fields):
        self.name = fields.name
        self.description = fields.description
        self.statement = fields.statement
        self.save()
        return self

    #@ExportMethod(NoneType, [DjangoId('Problem')], PCArg('self', 'MANAGE'), [CannotDeleteObject])
    def delete(self):
        logging.error('problem deleted') #TODO: Waiting for non-cascading deletes in django
        for test in self.tests.all():
            test.delete()
        self.privileges.all().delete()
        try:
            super(Problem, self).delete()
        except DatabaseError:
            raise CannotDeleteObject()

class ProblemEvents(Events):
    model = Problem
    on_insert = on_update = ['name']
    on_delete = []
