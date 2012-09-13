# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev  import Events
from satori.core.models import Entity

@ExportModel
class ComparisonResult(Entity):
    """Model. Description of a comparison.

    rights:
		VIEW
        MANAGE
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_comparison')
    

    comparison      = models.ForeignKey('Comparison', related_name='results', on_delete=models.PROTECT)
    submit_1        = models.ForeignKey('Submit', related_name='results_1', on_delete=models.PROTECT)
    submit_2        = models.ForeignKey('Submit', related_name='results_2', on_delete=models.PROTECT)
    result          = models.FloatField()
    

    class ExportMeta(object):
        fields = [('comparison', 'VIEW'), ('submit_1', 'VIEW'), ('submit_2', 'VIEW'), ('result', 'VIEW')]
        
    class RightsMeta(object):
        rights = ['VIEW_RESULTS', 'DELETE', 'ADD']

        inherit_VIEW_RESULTS = ['VIEW']
        inherit_DELETE = ['MANAGE']
        inherit_ADD = ['MANAGE']

    @classmethod
    def inherit_rights(cls):
        inherits = super(Contest, cls).inherit_rights()
        cls._inherit_add(inherits, 'VIEW_RESULTS', 'id', 'VIEW')
        cls._inherit_add(inherits, 'DELETE', 'id', 'MANAGE')
        cls._inherit_add(inherits, 'ADD', 'id', 'MANAGE')
        return inherits

    def save(self, *args, **kwargs):
        self.fixup_appearance()
        super(Comparison, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

	@ExportMethod(DjangoStruct('ComparisonResult'), [DjangoStruct('ComparisonResult')], PCPermit ('MANAGE_CONTESTS'), [CannotSetField])
    @staticmethod
    def create(fields):
        comparison = ComparisonResult()
        comparison.forbid_fields(fields, ['id'])
        comparison.update_fields(fields, ['comparison', 'submit_1', 'submit_2', 'result'])
        comparison.save()
        return comparison
        
    @ExportMethod(DjangoStruct('ComparisonResult'), [DjangoId('ComparisonResult'), DjangoStruct('ComparisonResult')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, ['id'])
        self.update_fields(fields, ['comparison', 'submit_1', 'submit_2', 'result'])
        self.save()
        return self

    @ExportMethod(NoneType, [DjangoId('ComparisonResult')], PCArg('self', 'MANAGE'), [CannotDeleteObject])
    def delete(self):
        super(ComparisonResult, self).delete()
        except models.ProtectedError as e:
            raise CannotDeleteObject()

class ComparisonResultEvents(Events):
    model = ComparisonResult
    on_insert = on_update = []#?????
    on_delete = []
