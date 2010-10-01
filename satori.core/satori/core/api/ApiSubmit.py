# vim:ts=4:sts=4:sw=4:expandtab

from types import NoneType
from satori.objects import Argument, ReturnValue
from satori.ars.wrapper import TypedList
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Submit, TestSuite, TestSuiteResult, TestResult
from satori.core.sec.tools import Token

submit = ModelWrapper(Submit)

submit.attributes('data')

@submit.method
@Argument('token', type=Token)
@Argument('self', type=Submit)
@Argument('test_suite', type=(TestSuite, NoneType))
@ReturnValue(type=TypedList(TestResult))
def get_test_suite_results(token, self, test_suite=None):
    if test_suite is None:
        test_suite = self.problem.default_test_suite
    return TestResult.objects.filter(submit=self, test__testsuite=test_suite)
        
@submit.method
@Argument('token', type=Token)
@Argument('self', type=Submit)
@Argument('test_suite', type=(TestSuite, NoneType))
@ReturnValue(type=(TestSuiteResult, NoneType))
def get_test_suite_result(token, self, test_suite=None):
    if test_suite is None:
        test_suite = self.problem.default_test_suite

    try:
        return TestSuiteResult.objects.get(submit=self, test_suite=test_suite)
    except TestSuiteResult.DoesNotExist:
        return None

@submit.method
@Argument('token', type=Token)
@Argument('self', type=Submit)
@Argument('test_suite', type=(TestSuite, NoneType))
@ReturnValue(type=(unicode, NoneType))
def get_test_suite_status(token, self, test_suite=None):
    test_suite_result = Submit_get_test_suite_result.implementation(token, self, test_suite)

    if test_suite_result is None:
        return None

    return test_suite_result.status

@submit.method
@Argument('token', type=Token)
@Argument('self', type=Submit)
@Argument('test_suite', type=(TestSuite, NoneType))
@ReturnValue(type=(unicode, NoneType))
def get_test_suite_report(token, self, test_suite=None):
    test_suite_result = Submit_get_test_suite_result.implementation(token, self, test_suite)

    if test_suite_result is None:
        return None

    return test_suite_result.report

submit._fill_module(__name__)

