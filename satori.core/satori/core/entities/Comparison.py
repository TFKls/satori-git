# vim:ts=4:sts=4:sw=4:expandtab

#import datetime
from django.db import models

from satori.core.dbev  import Events
from satori.core.models import Entity

@ExportModel
class Comparison(Entity):
    """Model. Description of a comparison.

    rights:
		VIEW
        MANAGE
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_comparison')
    
    ALGORITHM_CHOICES = (
		(0, 'Algorithm for C++'),
		(1, 'other ;) '),
	)

    problem_mapping = models.ForeignKey('ProblemMapping', related_name='comparisons+', on_delete=models.PROTECT)
    algorithm       = models.IntegerField(default=0, choices=ALGORITHM_CHOICES)
    test_suite      = models.ForeignKey('TestSuite', related_name='comparisons+', on_delete=models.PROTECT)
    regexp          = models.CharField(max_length=64, unique=False)
    creation_date   = models.DateTimeField(auto_now_add=True)
    execution_date  = models.DateTimeField(null=True)
    
    

    class ExportMeta(object):
        fields = [('problem_mapping', 'VIEW'), ('algorithm', 'VIEW'), ('test_suite', 'VIEW'), ('regexp', 'VIEW'), ('creation_date', 'VIEW'), ('execution_date', 'VIEW')]

    class RightsMeta(object):
        inherit_parent = 'problem_mapping'
        inherit_parent_MANAGE = ['MANAGE']

    @classmethod
    def inherit_rights(cls):
        inherits = super(Comparison, cls).inherit_rights()
        cls._inherit_add(inherits, 'MANAGE', 'problem_mapping', 'MANAGE')
        return inherits
        
    def save(self, *args, **kwargs):
        super(Comparison, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    @ExportMethod(DjangoStruct('Comparison'), [DjangoStruct('Comparison')], PCArgField('fields', 'problem_mapping', 'MANAGE'), [CannotSetField])
    @staticmethod
    def create(fields):
        comparison = Comparison()
        comparison.forbid_fields(fields, ['id', 'creation_date'])
        comparison.update_fields(fields, ['problem_mapping', 'algorithm', 'test_suite', 'regexp'])
        comparison.save()
        return comparison
        
    @ExportMethod(DjangoStruct('Comparison'), [DjangoId('Comparison'), DjangoStruct('Comparison')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, ['id', 'creation_date'])
        self.update_fields(fields, ['problem_mapping', 'algorithm', 'test_suite', 'regexp'])
        self.execution_date = datetime.now()
        self.save()
        return self

    @ExportMethod(bool, [DjangoId('Comparison')], PCArg('self', 'MANAGE'), [CannotSetField])
    def isExecute(self):
        return (self.execution_date is None)

    @ExportMethod(NoneType, [DjangoId('Comparison')], PCArg('self', 'MANAGE'), [CannotDeleteObject])
    def delete(self):
        try:
            # should be done with cascading, but currently will not work
            for cr in self.comparison_result.all():
                cr.delete()
                
            super(Comparison, self).delete()
        except models.ProtectedError as e:
            raise CannotDeleteObject()


class ComparisonEvents(Events):
    model = Comparison
    on_insert = on_update = []
    on_delete = []
