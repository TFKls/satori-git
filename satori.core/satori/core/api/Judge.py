# vim:ts=4:sts=4:sw=4:expandtab
"""
Judge helper procedures.
"""

from types import NoneType

from satori.objects import Argument, ReturnValue
from satori.core.models import TestResult, User
from satori.core.sec.tools import Token
from satori.ars.wrapper import Struct, StaticWrapper, TypedList
from satori.core.cwrapper import Attribute
from satori.core.judge_dispatcher import JudgeDispatcherClient
import Test as ApiTest
import Submit as ApiSubmit

judge = StaticWrapper('Judge')

SubmitToCheck = Struct('SubmitToCheck', (
    ('test_result', TestResult, True),
    ('test_contents', TypedList(Attribute), False),
    ('submit_contents', TypedList(Attribute), False)
))

@judge.method
@Argument('token', type=Token)
@ReturnValue(type=(SubmitToCheck, NoneType))
def get_next(token):
    u = User.objects.all()[0]
    next = JudgeDispatcherClient.get_instance().get_next(u)
    print next
    if next.test_result_id is None:
    	return None
    ret = {}
    ret['test_result'] = TestResult.objects.get(id=next.test_result_id)
    ret['test_contents'] = ApiTest.Test__Oa__get_list(token, ret['test_result'].test)
    ret['submit_contents'] = ApiSubmit.Submit__Oa__get_list(token, ret['test_result'].submit)
    return ret

@judge.method
@Argument('token', type=Token)
@Argument('test_result', type=TestResult)
@Argument('result', type=TypedList(Attribute))
@ReturnValue(type=NoneType)
def set_result(token, test_result, result):
    pass

