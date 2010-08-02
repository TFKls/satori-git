# vim:ts=4:sts=4:sw=4:expandtab

from satori.objects import Argument, ReturnValue
from satori.ars.wrapper import TypedList
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Contest, Contestant, User
from satori.core.sec import Token

contest = ModelWrapper(Contest)

@contest.method
@Argument('token', type=Token)
@Argument('self', type=Contest)
@Argument('user', type=User)
@ReturnValue(type=Contestant)
def find_contestant(token, self, user):
    return Contestant.objects.filter(contest=self, accepted=True, children__id=user.id)[0]

@contest.find_contestant.can
def find_contestant_check(token, self, user):
    return True
#    if token.user == user:
#        self.demand_right(token, 'VIEW')
#    else:
#        self.demand_right(token, 'MODERATE')

@contest.method
@Argument('token', type=Token)
@Argument('self', type=Contest)
@Argument('user_list', type=TypedList(User))
@Argument('accepted', type=bool, default=False)
@ReturnValue(type=Contestant)
def create_contestant(token, self, user_list, accepted):
    u = User.objects.get(id=token.user.id)
    if self.joining == 'Public':
        if token.user not in user_list: 
            self.demand_right('MODERATE')
        elif accepted and len(user_list) == 1:
            pass
        elif not accepted:
            pass
        else:
            self.demand_right('MODERATE')
    elif self.joining == 'Moderated':
        if token.user not in user_list or accepted:
            self.demand_right('MODERATE')
    else:
        self.demand_right('MODERATE')

    c = Contestant()
    c.accepted = accepted
    c.contest = self
    c.save()
    for user in user_list:
        rm = RoleMapping()
        rm.parent = c
        rm.child = user
        rm.save()

contest._fill_module(__name__)
