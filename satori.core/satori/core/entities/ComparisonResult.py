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
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_comparisonresult')
    

    comparison      = models.ForeignKey('Comparison', related_name='results', on_delete=models.PROTECT)
    submit_1        = models.ForeignKey('Submit', related_name='comparisonresults+', on_delete=models.PROTECT)
    submit_2        = models.ForeignKey('Submit', related_name='comparisonresults+', on_delete=models.PROTECT)  
    hidden          = models.BooleanField()
    who_hid         = models.ForeignKey('User',  related_name='comparisonresults+', on_delete=models.PROTECT, null=True)
    result          = models.FloatField()
    

    class ExportMeta(object):
        fields = [('comparison', 'VIEW'), ('submit_1', 'VIEW'), ('submit_2', 'VIEW'), ('hidden', 'VIEW'), ('who_hid', 'VIEW'), ('result', 'VIEW')]
        
    class RightsMeta(object):
        inherit_parent = 'comparison'
        inherit_parent_VIEW = ['VIEW']
        inherit_parent_MANAGE = ['MANAGE']

    @classmethod
    def inherit_rights(cls):
        inherits = super(ComparisonResult, cls).inherit_rights()
        cls._inherit_add(inherits, 'VIEW', 'comparison', 'VIEW')
        cls._inherit_add(inherits, 'MANAGE', 'comparison', 'MANAGE')
        return inherits

    def __str__(self):
        return self.name

    @ExportMethod(DjangoStruct('ComparisonResult'), [DjangoStruct('ComparisonResult')], PCArgField('fields', 'comparison', 'MANAGE'), [CannotSetField])
    @staticmethod
    def create(fields):
        comparisonres = ComparisonResult()
        comparisonres.forbid_fields(fields, ['id', 'who_hid'])
        comparisonres.update_fields(fields, ['comparison', 'submit_1', 'submit_2', 'hidden', 'result'])
        comparisonres.save()
        return comparisonres

    @ExportMethod(DjangoStruct('ComparisonResult'), [DjangoId('ComparisonResult'), DjangoStruct('ComparisonResult')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, ['id'])
        self.update_fields(fields, ['comparison', 'submit_1', 'submit_2', 'hidden', 'who_hid', 'result'])
        self.save()
        return self

    @ExportMethod(NoneType, [DjangoId('ComparisonResult')], PCArg('self', 'MANAGE'), [CannotDeleteObject])
    def delete(self):
        try:
            super(ComparisonResult, self).delete()
        except models.ProtectedError as e:
            raise CannotDeleteObject()

class ComparisonResultEvents(Events):
    model = ComparisonResult
    on_insert = on_update = []
    on_delete = []
