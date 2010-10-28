# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models

from satori.core.export        import ExportMethod
from satori.core.export_django import ExportModel, DjangoStructList
from satori.core.dbev               import Events

from satori.core.models import Entity

@ExportModel
class Submit(Entity):
    """Model. Single problem solution (within or outside of a Contest).
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Entity, parent_link=True, related_name='cast_submit')

    contestant  = models.ForeignKey('Contestant')
    problem     = models.ForeignKey('ProblemMapping')
    time        = models.DateTimeField(auto_now_add=True)

    generate_attribute_group('Submit', 'data', 'VIEW', 'EDIT', globals(), locals())

    class ExportMeta(object):
        fields = [('contestant', 'VIEW'), ('problem', 'VIEW'), ('time', 'VIEW')]

    def save(self):
        self.fixup_data()
        super(Submit, self).save()

    def inherit_right(self, right):
        right = str(right)
        ret = super(Submit, self).inherit_right(right)
        if right == 'VIEW':
            ret.append((self.contestant.contest,'OBSERVE'))
        if right == 'OVERRIDE':
            ret.append((self.contestant.contest,'MANAGE'))
        return ret

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

