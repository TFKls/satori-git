# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models
from satori.dbev import Events
from satori.core.models import Entity
from satori.core.models import AttributeGroup

class Submit(Entity):
    """Model. Single problem solution (within or outside of a Contest).
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Entity, parent_link=True, related_name='cast_submit')

    contestant  = models.ForeignKey('Contestant')
    problem     = models.ForeignKey('ProblemMapping')
    data    = models.OneToOneField('AttributeGroup', related_name='group_submit_data')
    time        = models.DateTimeField(auto_now_add=True)

    def save(self):
        try:
            x = self.data
        except AttributeGroup.DoesNotExist:
            data = AttributeGroup()
            data.save()
            self.data = data

        super(Submit, self).save()

    def inherit_right(self, right):
        right = str(right)
        ret = super(Submit, self).inherit_right(right)
        if right == 'VIEW':
            ret.append((self.contestant.contest,'OBSERVE'))
        if right == 'OVERRIDE':
            ret.append((self.contestant.contest,'MANAGE'))
        return ret

class SubmitEvents(Events):
    model = Submit
    on_insert = on_update = ['owner', 'problem']
    on_delete = []


#! module api

from types import NoneType
from satori.objects import Argument, ReturnValue
from satori.ars.wrapper import TypedList, WrapperClass
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Submit, TestSuite, TestSuiteResult, TestResult
from satori.core.sec.tools import Token

class ApiSubmit(WrapperClass):
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


