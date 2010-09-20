# vim:ts=4:sts=4:sw=4:expandtab

from satori.objects import Argument, ReturnValue
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Problem, Global, Privilege
from satori.core.sec import Token

problem = ModelWrapper(Problem)

problem.attributes('default_test_data')

@problem.method
@Argument('token', type=Token)
@Argument('name', type=str)
@ReturnValue(type=Problem)
def create_problem(token, name):
    o = Problem()
    o.name = name
    o.save()
    p = Privilege(role = token.user, object = o, right='MANAGE')
    p.save()
    return o
@problem.create_problem.can
def create_problem_check(token, name):
    return Global.get_instance().demand_right(token, 'MANAGE_PROBLEMS')


problem._fill_module(__name__)

