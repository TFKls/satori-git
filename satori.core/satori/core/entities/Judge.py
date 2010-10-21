#! module api
"""
Judge helper procedures.
"""

from types import NoneType

from satori.objects import Argument, ReturnValue
from satori.core.models import TestResult, User
from satori.core.sec.tools import Token
from satori.ars.wrapper import Struct, StaticWrapper, TypedList, TypedMap, WrapperClass
from satori.core.cwrapper import Attribute, AnonymousAttribute
from satori.core.checking.check_queue_client import CheckQueueClient

from satori.core.api import ApiEntity, ApiTest, ApiTestResult, ApiSubmit

SubmitToCheck = Struct('SubmitToCheck', (
    ('test_result', TestResult, True),
    ('test_data', TypedMap(unicode, Attribute), False),
    ('submit_data', TypedMap(unicode, Attribute), False)
))

class ApiJudge(WrapperClass):
    judge = StaticWrapper('Judge')

    @judge.method
    @Argument('token', type=Token)
    @ReturnValue(type=(SubmitToCheck, NoneType))
    def get_next(token):
        u = token.user
        next = CheckQueueClient.get_instance().get_next(u)
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
        ApiEntity.Entity_oa_set_map.implementation(token, test_result, result)
        test_result.pending = False
        test_result.save()

