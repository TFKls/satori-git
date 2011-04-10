# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class TemporarySubmit(Entity):
    """
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_temporary_submit')

    pending       = models.BooleanField(default=True)
    date_created  = models.DateTimeField(auto_now_add=True)
    tester        = models.ForeignKey('Role', null=True, related_name='+', on_delete=models.SET_NULL)
    owner         = models.ForeignKey('Role', related_name='+', on_delete=models.CASCADE)

    test_data     = AttributeGroupField(PCArg('self', 'MANAGE'), PCArg('self', 'MANAGE'), '')
    submit_data   = AttributeGroupField(PCArg('self', 'MANAGE'), PCArg('self', 'MANAGE'), '')
    result        = AttributeGroupField(PCArg('self', 'MANAGE'), PCArg('self', 'MANAGE'), '')

    class ExportMeta(object):
        fields = [('pending', 'MANAGE'), ('date_created', 'MANAGE')]

    def save(self, *args, **kwargs):
        self.fixup_test_data()
        self.fixup_submit_data()
        self.fixup_result()
        super(TemporarySubmit, self).save(*args, **kwargs)

    @ExportMethod(DjangoStruct('TemporarySubmit'), [TypedMap(unicode, AnonymousAttribute), TypedMap(unicode, AnonymousAttribute)],
            PCAnd(PCGlobal('TEMPORARY_SUBMIT'), PCEachValue('test_data', PCRawBlob('item')), PCEachValue('submit_data', PCRawBlob('item'))))
    @staticmethod
    def create(test_data, submit_data):
        ts = TemporarySubmit.objects.create(owner=token_container.token.role)
        ts.test_data_set_map(test_data)
        ts.submit_data_set_map(submit_data)
        Privilege.grant(token_container.token.role, ts, 'MANAGE')
        RawEvent().send(Event(type='checking_new_temporary_submit', id=ts.id))
        return ts
        
    @ExportMethod(NoneType, [DjangoId('TemporarySubmit')], PCArg('self', 'MANAGE'), [CannotDeleteObject])
    def delete(self):
        try:
            super(TemporarySubmit, self).delete()
        except models.ProtectedError as e:
            raise CannotDeleteObject()

class TemporarySubmitEvents(Events):
    model = TemporarySubmit
    on_insert = on_update = on_delete = []
