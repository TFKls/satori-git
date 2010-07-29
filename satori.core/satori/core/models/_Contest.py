# vim:ts=4:sts=4:sw=4:expandtab
from django.db import models
from satori.dbev import events
from satori.ars import wrapper
from satori.core import cwrapper
from satori.ars.django_ import DjangoModelType
from satori.objects import Argument, ReturnValue
from satori.core.models._Contestant import Contestant
from satori.core.models._Object import Object
from satori.core.models._User import User
from satori.core.models.modules import AGGREGATORS3

class Contest(Object):
    """Model. Description of a contest.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_contest')
    
    joiningChoices = [ ('Private', 'Private'),('Moderated','Moderated'),('Public','Public') ]
    name        = models.CharField(max_length=50, unique=True)
    problems    = models.ManyToManyField('Problem', through='ProblemMapping')
    joining     = models.CharField(max_length=30, choices=joiningChoices)
    aggregator3 = models.CharField(max_length=128, choices=AGGREGATORS3)
    def __unicode__(self):
        return self.name
    # TODO: add presentation options

    
class ContestEvents(events.Events):
    model = Contest
    on_insert = on_update = ['name']
    on_delete = []

class ContestWrapper(wrapper.WrapperClass):
    contest = cwrapper.ModelWrapper(Contest)

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
        return Contestant.filter(contest=self, accepted=True, children__id=user.id)[0]

    @contest.method
    @Argument('token', type=str)
    @Argument('self', type=Contest)
    @Argument('user_list', type=wrapper.TypedList(User))
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
