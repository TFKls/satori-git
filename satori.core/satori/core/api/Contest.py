# vim:ts=4:sts=4:sw=4:expandtab

from satori.objects import Argument, ReturnValue
from satori.ars.wrapper import TypedList
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Contest, Contestant, User, ProblemMapping, Submit, Global, Role, RoleMapping, Privilege
from satori.core.sec import Token

contest = ModelWrapper(Contest)

@contest.method
@Argument('token', type=Token)
@Argument('self', type=Contest)
@Argument('user', type=User)
@ReturnValue(type=Contestant)
def find_contestant(token, self, user):
    return Contestant.objects.filter(contest=self, children__id=user.id)[0]
@contest.find_contestant.can
def find_contestant_check(token, self, user):
    return token.user == user or self.demand_right(token, 'MANAGE')

@contest.method
@Argument('token', type=Token)
@Argument('self', type=Contest)
@Argument('user_list', type=TypedList(User))
@ReturnValue(type=Contestant)
def create_contestant(token, self, user_list):
    c = Contestant()
    c.accepted = True
    c.contest = self
    c.save()
    RoleMapping(parent = self.contestant_role, child = c).save()
    for user in user_list:
        RoleMapping(parent = c, child = user).save()
@contest.create_contestant.can
def create_contestant_check(token, self, user_list):
    return self.demand_right(token, 'MANAGE')

@contest.method
@Argument('token', type=Token)
@Argument('name', type=str)
@ReturnValue(type=Contest)
def create_contest(token, name):
    c = Contest()
    c.name = name
    r = Role(name=name+'_contestant', )
    r.save()
    c.contestant_role = r
    c.save()
    p = Privilege(role = token.user, object = c, right='MANAGE')
    p.save()
    return c
@contest.create_contest.can
def create_contest_check(token, name):
    return Global.get_instance().demand_right(token, 'MANAGE_CONTESTS')

@contest.method
@Argument('token', type=Token)
@Argument('self', type=Contest)
@ReturnValue(type=Contestant)
def join_contest(token, self):
    c = Contestant()
    c.contest = self
    c.accepted = bool(self.demand_right(token, 'JOIN'))
    c.save()
    if c.accepted:
        RoleMapping(parent = self.contestant_role, child = c).save()
    RoleMapping(child = token.user, parent = c).save()
    return c
@contest.join_contest.can
def join_contest_check(token, self):
    return self.demand_right(token, 'APPLY')

@contest.method
@Argument('token', type=Token)
@Argument('self', type=Contest)
@Argument('contestant', type=Contestant)
@ReturnValue(type=Contestant)
def accept_contestant(token, self, contestant):
    if contestant.contest != self:
    	raise "Go away"
    contestant.accepted = True
    RoleMapping(parent = self.contestant_role, child = c).save()
#TODO: RoleMapping may exist!
    contestant.save()
    return contestant
@contest.accept_contestant.can
def accept_contestant_check(token, self, contestant):
    return self.demand_right(token, 'MANAGE')

@contest.method
@Argument('token', type=Token)
@Argument('self', type=Contest)
@Argument('problem_mapping', type=ProblemMapping)
@Argument('content', type=str)
@Argument('filename', type=str)
@ReturnValue(type=Submit)
def submit(token, self, problem_mapping, content, filename):
    contestant = self.find_contestant(token, token.user)
    if contestant.contest != self:
    	raise "Go away"
    if problem_mapping.contest != self:
    	raise "Go away"
    submit = Submit()
    submit.contestant = contestant
    submit.problem = problem_mapping
#TODO: submit.open_attr['content'] = content
#TODO: submit.open_attr['filename'] = filename
	submit.save()
	return submit
@contest.submit.can
def submit_check(token, self, problem_mapping, content, filename):
    return problem_mapping.demand_right(token, 'SUBMIT')




contest._fill_module(__name__)
