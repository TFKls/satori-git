# vim:ts=4:sts=4:sw=4:expandtab
"""
Judge helper procedures.
"""

from types import NoneType

from satori.objects import Argument, ReturnValue
from satori.core.models import TestResult, User
from satori.core.sec.tools import Token
from satori.ars.wrapper import Struct, StaticWrapper, TypedList, TypedMap
from satori.core.cwrapper import Attribute, AnonymousAttribute
from satori.core.judge_dispatcher import JudgeDispatcherClient

import ApiObject
import ApiTest
import ApiTestResult
import ApiSubmit

judge = StaticWrapper('Judge')

SubmitToCheck = Struct('SubmitToCheck', (
    ('test_result', TestResult, True),
    ('test_data', TypedMap(unicode, Attribute), False),
    ('submit_data', TypedMap(unicode, Attribute), False)
))

@judge.method
@Argument('token', type=Token)
@ReturnValue(type=(SubmitToCheck, NoneType))
def get_next(token):
    u = token.user
    next = JudgeDispatcherClient.get_instance().get_next(u)
    if next.test_result_id is None:
    	return None
    ret = {}
    ret['test_result'] = TestResult.objects.get(id=next.test_result_id)
    ret['test_data'] = ApiTest.Test_data_get_map.implementation(token, ret['test_result'].test)
    ret['submit_data'] = ApiSubmit.Submit_data_get_map.implementation(token, ret['test_result'].submit)
    return ret

@judge.method
@Argument('token', type=Token)
@Argument('test_result', type=TestResult)
@Argument('result', type=TypedMap(unicode, AnonymousAttribute))
@ReturnValue(type=NoneType)
def set_result(token, test_result, result):
    ApiObject.Object_oa_set_map.implementation(token, test_result, result)
    test_result.pending = False
    test_result.save()
    #JudgeDispatcherClient.get_instance().set_result(test_result)

