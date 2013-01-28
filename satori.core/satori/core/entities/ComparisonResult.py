# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev  import Events
from satori.core.models import Entity

@ExportModel
class ComparisonResult(Entity):
    """Model. Description of a comparison result.

    rights:
		VIEW
        MANAGE
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_comparisonresult')

    comparison      = models.ForeignKey('Comparison', related_name='results', on_delete=models.CASCADE)
    submit_1        = models.ForeignKey('Submit', related_name='comparisonresults+', on_delete=models.CASCADE)
    submit_2        = models.ForeignKey('Submit', related_name='comparisonresults+', on_delete=models.CASCADE)  
    resolved        = models.BooleanField()
    resolver        = models.ForeignKey('User',  related_name='comparisonresults+', on_delete=models.SET_NULL, null=True)
    result          = models.FloatField(null=True)
    
    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('comparison', 'submit_1', 'submit_2'),)

    class ExportMeta(object):
        fields = [('comparison', 'VIEW'), ('submit_1', 'VIEW'), ('submit_2', 'VIEW'), ('resolved', 'VIEW'), ('resolver', 'VIEW'), ('result', 'VIEW')]
        
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
        comparisonres.forbid_fields(fields, ['id', 'resolver'])
        comparisonres.update_fields(fields, ['comparison', 'submit_1', 'submit_2', 'resolved'])
        if comparisonres.submit_1.id > comparisonres.submit_2.id:
            z = comparisonres.submit_1
            comparisonres.submit_1 = comparisonres.submit_2
            comparisonres.submit_2 = z
        if comparisonres.resolved:
            comparisonres.resolver = token_container.token_user
        comparisonres.save()
        return comparisonres

    @ExportMethod(DjangoStruct('ComparisonResult'), [DjangoId('ComparisonResult'), DjangoStruct('ComparisonResult')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, ['id', 'resolver', 'submit_1', 'submit_2'])
        modified = self.update_fields(fields, ['comparison', 'resolved', 'result'])
        if 'resolved' in modified:
            if self.resolved:
                self.resolver = token_container.token_user
            else:
                self.resolver = None
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
