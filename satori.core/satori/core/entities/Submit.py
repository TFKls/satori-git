# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity, Contest

@ExportModel
class Submit(Entity):
    """Model. Single problem solution (within or outside of a Contest).
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_submit')

    contestant    = models.ForeignKey('Contestant', related_name='submits', on_delete=models.PROTECT)
    problem       = models.ForeignKey('ProblemMapping', related_name='submits', on_delete=models.PROTECT)
    time          = models.DateTimeField(auto_now_add=True)

    data          = AttributeGroupField(PCArg('self', 'VIEW'), PCDeny(), '')
    overrides     = AttributeGroupField(PCArg('self', 'MANAGE'), PCDeny(), '')

    class ExportMeta(object):
        fields = [('contestant', 'VIEW'), ('problem', 'VIEW'), ('time', 'VIEW')]

    class RightsMeta(object):
        rights = ['VIEW_CONTENTS', 'VIEW_RESULTS']
        inherit_parent = 'contestant'

        inherit_VIEW = ['VIEW_CONTENTS', 'VIEW_RESULTS']
        inherit_parent_MANAGE = ['MANAGE']
        inherit_VIEW_CONTENTS = ['MANAGE']
        inherit_parent_VIEW_CONTENTS = ['VIEW_SUBMIT_CONTENTS']
        inherit_VIEW_RESULTS = ['MANAGE']
        inherit_parent_VIEW_RESULTS = ['VIEW_SUBMIT_RESULTS']

    @classmethod
    def inherit_rights(cls):
        inherits = super(Submit, cls).inherit_rights()
        cls._inherit_add(inherits, 'VIEW', 'id', 'OBSERVE')
        cls._inherit_add(inherits, 'OBSERVE', 'contestant', 'OBSERVE')
        cls._inherit_add(inherits, 'MANAGE', 'contestant', 'MANAGE')
        return inherits

    def save(self, *args, **kwargs):
        self.fixup_overrides()
        self.fixup_data()
        super(Submit, self).save(*args, **kwargs)

    @ExportMethod(DjangoStruct('Submit'), [DjangoStruct('Submit'), Binary, unicode], PCArgField('fields', 'problem', 'SUBMIT'), [CannotSetField])
    @staticmethod
    def create(fields, content, filename):
        submit = Submit()
        submit.contestant = fields.problem.contest.find_contestant(token_container.token.role)
        submit.forbid_fields(fields, ['id', 'contestant', 'time'])
        submit.update_fields(fields, ['problem'])
        submit.save()
        blob = submit.data_set_blob('content', filename=filename)
        blob.write(content)
        blob.close()
        RawEvent().send(Event(type='checking_new_submit', id=submit.id))
        return submit

    @ExportMethod(DjangoStruct('Submit'), [DjangoStruct('Submit'), Binary, unicode, TypedMap(DjangoId('Test'), TypedMap(unicode, AnonymousAttribute))], PCGlobal('ADMIN'), [CannotSetField])
    @staticmethod
    def inject(fields, content, filename, test_results):
        submit = Submit()
        submit.forbid_fields(fields, ['id'])
        submit.update_fields(fields, ['contestant', 'time', 'problem'])
        submit.save()
        submit.update_fields(fields, ['time'])
        submit.save()
        blob = submit.data_set_blob('content', filename=filename)
        blob.write(content)
        blob.close()
        for test, result in test_results.iteritems():
            tr = TestResult(submit=submit, test=test, tester=token_container.token.role, pending=False)
            tr.save()
            tr.oa_set_map(result)
        RawEvent().send(Event(type='checking_new_submit', id=submit.id))
        return submit
        
    @ExportMethod(NoneType, [DjangoId('Submit')], PCArg('self', 'MANAGE'), [CannotDeleteObject])
    def delete(self):
        try:
            super(Submit, self).delete()
        except models.ProtectedError as e:
            raise CannotDeleteObject()

    @ExportMethod(NoneType, [DjangoId('Submit'), TypedMap(unicode, AnonymousAttribute)], PCAnd(PCArg('self', 'MANAGE'), PCEachValue('overrides', PCRawBlob('item'))))
    def override(self, overrides):
        self.overrides_set_map(overrides)
        self.rejudge_test_suite_results()

    @ExportMethod(unicode, [DjangoId('Submit'), DjangoId('TestSuite')], PCArg('self', 'VIEW_RESULTS'))
    def get_test_suite_status(self, test_suite=None):
        if test_suite is None:
            test_suite = self.problem.default_test_suite
        try:
            return TestSuiteResult.objects.get(submit=self, test_suite=test_suite).status
        except TestSuiteResult.DoesNotExist:
            return None
    
    @ExportMethod(unicode, [DjangoId('Submit'), DjangoId('TestSuite')], PCArg('self', 'VIEW_RESULTS'))
    def get_test_suite_report(self, test_suite=None):
        if test_suite is None:
            test_suite = self.problem.default_test_suite
        try:
            return TestSuiteResult.objects.get(submit=self, test_suite=test_suite).report
        except TestSuiteResult.DoesNotExist:
            return None

    @ExportMethod(NoneType, [DjangoId('Submit')], PCArg('self', 'MANAGE'))
    def rejudge_test_results(self):
        RawEvent().send(Event(type='checking_rejudge_submit_test_results', id=self.id))

    @ExportMethod(NoneType, [DjangoId('Submit')], PCArg('self', 'MANAGE'))
    def rejudge_test_suite_results(self):
        RawEvent().send(Event(type='checking_rejudge_submit_test_suite_results', id=self.id))

class SubmitEvents(Events):
    model = Submit
    on_insert = on_update = ['owner', 'problem']
    on_delete = []
