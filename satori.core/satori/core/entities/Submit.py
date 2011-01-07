# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class Submit(Entity):
    """Model. Single problem solution (within or outside of a Contest).
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_submit')

    contestant    = models.ForeignKey('Contestant', related_name='submits')
    problem       = models.ForeignKey('ProblemMapping', related_name='submits')
    time          = models.DateTimeField(auto_now_add=True)

    data          = AttributeGroupField(PCArg('self', 'VIEW'), PCDeny(), '')
    overrides     = AttributeGroupField(PCArg('self', 'MANAGE'), PCDeny(), '')

    class ExportMeta(object):
        fields = [('contestant', 'VIEW'), ('problem', 'VIEW'), ('time', 'VIEW')]

    @classmethod
    def inherit_rights(cls):
        inherits = super(Submit, cls).inherit_rights()
        cls._inherit_add(inherits, 'VIEW', 'id', 'OBSERVE')
        cls._inherit_add(inherits, 'OBSERVE', 'contestant', 'OBSERVE')
        return inherits

    def save(self, *args, **kwargs):
        self.fixup_data()
        super(Submit, self).save(*args, **kwargs)

    @ExportMethod(DjangoStruct('Submit'), [DjangoStruct('Submit'), unicode, unicode], PCArgField('fields', 'problem', 'SUBMIT'), [CannotSetField])
    @staticmethod
    def create(fields, content, filename):
        submit = Submit()
        submit.contestant = fields.problem.contest.find_contestant(token_container.token.role)
        submit.forbid_fields(fields, ['id', 'contestant', 'time'])
        submit.update_fields(fields, ['problem'])
        submit.save()
        Privilege.grant(submit.contestant, submit, 'VIEW')
        blob = submit.data_set_blob('content', filename=filename)
        blob.write(content)
        blob.close()
        RawEvent().send(Event(type='checking_new_submit', id=submit.id))
        return submit

    @ExportMethod(NoneType, [DjangoId('Submit'), TypedMap(unicode, AnonymousAttribute)], PCAnd(PCArg('self', 'MANAGE'), PCEachValue('overrides', PCRawBlob('item'))))
    def override(self, overrides):
        self.overrides_set_map(overrides)

    @ExportMethod(DjangoStructList('TestResult'), [DjangoId('Submit'), DjangoId('TestSuite')], PCArg('self', 'VIEW'))
    def get_test_suite_results(self, test_suite=None):
        if test_suite is None:
            test_suite = self.problem.default_test_suite
        return TestResult.objects.filter(submit=self, test__testsuite=test_suite)
            
    @ExportMethod(DjangoStruct('TestSuiteResult'), [DjangoId('Submit'), DjangoId('TestSuite')], PCArg('self', 'VIEW'))
    def get_test_suite_result(self, test_suite=None):
        if test_suite is None:
            test_suite = self.problem.default_test_suite
        try:
            return TestSuiteResult.objects.get(submit=self, test_suite=test_suite)
        except TestSuiteResult.DoesNotExist:
            return None

    @ExportMethod(unicode, [DjangoId('Submit'), DjangoId('TestSuite')], PCArg('self', 'VIEW'))
    def get_test_suite_status(self, test_suite=None):
        test_suite_result = self.get_test_suite_result(test_suite)
        if test_suite_result is None:
            return None
        return test_suite_result.status
    
    @ExportMethod(unicode, [DjangoId('Submit'), DjangoId('TestSuite')], PCArg('self', 'VIEW'))
    def get_test_suite_report(self, test_suite=None):
        test_suite_result = self.get_test_suite_result(test_suite)
        if test_suite_result is None:
            return None
        return test_suite_result.report

class SubmitEvents(Events):
    model = Submit
    on_insert = on_update = ['owner', 'problem']
    on_delete = []
