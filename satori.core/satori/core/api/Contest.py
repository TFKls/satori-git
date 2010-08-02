# vim:ts=4:sts=4:sw=4:expandtab

from satori.objects import Argument, ReturnValue
from satori.ars.wrapper import TypedList
from satori.core.cwrapper import ModelWrapper
from satori.core.models import Contest, Contestant, User

contest = ModelWrapper(Contest)

@contest.method
@Argument('token', type=str)
@Argument('self', type=Contest)
@Argument('user', type=User)
@ReturnValue(type=Contestant)
def find_contestant(token, self, user):
#        from satori.core.sec import Token
#        if Token(token).user == user:
#            self.demand_right(token, 'VIEW')
#        else:
#            self.demand_right(token, 'MODERATE')
    return Contestant.objects.filter(contest=self, accepted=True, children__id=user.id)[0]

@contest.method
@Argument('token', type=str)
@Argument('self', type=Contest)
@Argument('user_list', type=TypedList(User))
@Argument('accepted', type=bool, default=False)
@ReturnValue(type=Contestant)
def create_contestant(token, self, user_list, accepted):
    from satori.core.sec import Token
    u = User.objects.get(id=Token(token).user.id)
    if self.joining == 'Public':
        if Token(token).user not in user_list: 
            self.demand_right('MODERATE')
        elif accepted and len(user_list) == 1:
            pass
        elif not accepted:
            pass
        else:
            self.demand_right('MODERATE')
    elif self.joining == 'Moderated':
        if Token(token).user not in user_list or accepted:
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
