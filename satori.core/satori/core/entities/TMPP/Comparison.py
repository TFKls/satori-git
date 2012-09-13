# vim:ts=4:sts=4:sw=4:expandtab

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
		(0, 'Algorithm for C++')
		(1, 'other ;) ')
	)

    problem         = models.ForeignKey('Problem', related_name='problems', on_delete=models.PROTECT)
    algorithm       = models.IntegerField(default=0, choices=ALGORITHM_CHOICES)
    test_suite      = models.ForeignKey('TestSuite', related_name='test_suites', on_delete=models.PROTECT)
    regexp          = models.CharField(max_length=64, unique=False)
    

    class ExportMeta(object):
        fields = [('problem', 'VIEW'), ('algorithm', 'VIEW'), ('test_suite', 'VIEW'), ('regexp', 'VIEW')]
        
    class RightsMeta(object):
        rights = ['VIEW_COMPARISONS', 'DELETE', 'ADD']

        inherit_VIEW_COMPARISONS = ['VIEW']
        inherit_DELETE = ['MANAGE']
        inherit_ADD = ['MANAGE']

    @classmethod
    def inherit_rights(cls):
        inherits = super(Contest, cls).inherit_rights()
        cls._inherit_add(inherits, 'VIEW_COMPARISONS', 'id', 'VIEW')
        cls._inherit_add(inherits, 'DELETE', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'ADD', 'id', 'MANAGE')
        return inherits

    def save(self, *args, **kwargs):
        self.fixup_appearance()
        super(Comparison, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

        
    @ExportMethod(DjangoStruct('Comparison'), [DjangoStruct('Comparison')], PCPermit ('MANAGE_CONTESTS'), [CannotSetField])
    @staticmethod
    def create(fields):
        comparison = Comparison()
        comparison.forbid_fields(fields, ['id'])
        comparison.update_fields(fields, ['problem', 'algorithm', 'test_suite', 'regexp'])
        comparison.save()
        return comparison
        
    @ExportMethod(DjangoStruct('Comparison'), [DjangoId('Comparison'), DjangoStruct('Comparison')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, ['id'])
        self.update_fields(fields, ['problem', 'algorithm', 'test_suite', 'regexp'])
        self.save()
        return self

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
    on_insert = on_update = []#?????
    on_delete = []
