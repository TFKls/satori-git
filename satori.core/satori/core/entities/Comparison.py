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

    problem             = models.ForeignKey('ProblemMapping', related_name='comparisons+', on_delete=models.CASCADE)
    algorithm           = models.IntegerField(default=0, choices=ALGORITHM_CHOICES)
    test_suite          = models.ForeignKey('TestSuite', related_name='comparisons+', on_delete=models.PROTECT)
    result_filter       = models.CharField(max_length=64, unique=False)
    date_created        = models.DateTimeField(auto_now_add=True)
    date_last_executed  = models.DateTimeField(null=True)
    
    

    class ExportMeta(object):
        fields = [('problem', 'VIEW'), ('algorithm', 'VIEW'), ('test_suite', 'VIEW'), ('result_filter', 'VIEW'), ('date_created', 'VIEW'), ('date_last_executed', 'VIEW')]

    class RightsMeta(object):
        inherit_parent = 'problem'
        inherit_parent_MANAGE = ['MANAGE']

    @classmethod
    def inherit_rights(cls):
        inherits = super(Comparison, cls).inherit_rights()
        cls._inherit_add(inherits, 'MANAGE', 'problem', 'MANAGE')
        return inherits
        
    def save(self, *args, **kwargs):
        super(Comparison, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    @ExportMethod(DjangoStruct('Comparison'), [DjangoStruct('Comparison')], PCArgField('fields', 'problem', 'MANAGE'), [CannotSetField])
    @staticmethod
    def create(fields):
        comparison = Comparison()
        comparison.forbid_fields(fields, ['id', 'date_created'])
        comparison.update_fields(fields, ['problem', 'algorithm', 'test_suite', 'result_filter'])
        comparison.save()
        return comparison
        
    @ExportMethod(DjangoStruct('Comparison'), [DjangoId('Comparison'), DjangoStruct('Comparison')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, ['id', 'date_created'])
        self.update_fields(fields, ['problem', 'algorithm', 'test_suite', 'result_filter'])
        self.save()
        return self

    @ExportMethod(None, [DjangoId('Comparison')], PCArg('self', 'MANAGE'), [CannotSetField])
    def updateExecuteDate(self):
        self.date_last_executed = datetime.now()

    @ExportMethod(bool, [DjangoId('Comparison')], PCArg('self', 'MANAGE'), [CannotSetField])
    def isExecute(self):
        return (self.date_last_executed is None)

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
