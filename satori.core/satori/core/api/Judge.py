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
    return {'test_result': TestResult.objects.get(id=next.test_result_id), 'test_contents': [], 'submit_contents': []}

@judge.method
@Argument('token', type=Token)
@Argument('test_result', type=TestResult)
@Argument('result', type=TypedList(Attribute))
@ReturnValue(type=NoneType)
def set_result(token, test_result, result):
    pass

