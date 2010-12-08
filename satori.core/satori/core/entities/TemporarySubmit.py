# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev  import Events

from satori.core.models import Entity

@ExportModel
class TemporarySubmit(Entity):

    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_temporary_submit')

    pending      = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)

    generate_attribute_group('TemporarySubmit', 'test_data', 'MANAGE', 'MANAGE', globals(), locals())
    generate_attribute_group('TemporarySubmit', 'submit_data', 'MANAGE', 'MANAGE', globals(), locals())
    generate_attribute_group('TemporarySubmit', 'result', 'MANAGE', 'MANAGE', globals(), locals())

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
        ts = TemporarySubmit.objects.create()

        ts.test_data_set_map(test_data)
        ts.submit_data_set_map(test_data)

        Privilege.grant(token_container.token.role, ts, 'MANAGE')

        return ts

