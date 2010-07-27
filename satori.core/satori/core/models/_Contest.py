from django.db import models
from satori.dbev import events
from satori.ars import django_
from satori.core.models._Object import Object
from satori.core.models._Contestant import Contestant
from satori.core.models._User import User
from satori.core.models.modules import AGGREGATORS3
from satori.objects import ReturnValue, Argument
import typed

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

class ContestOpers(django_.Opers):
    contest = django_.ModelProceduresProvider(Contest)
    
    @contest.method
    @ReturnValue(type=Contestant)
    @Argument('token', type=str)
    @Argument('contest', type=Contest)
    #@Argument('user_list', type=typed.List(User))
    @Argument('user_list', type=None)
    def create_contestant(contest, user_list):
        c = Contestant()
        c.contest = contest
        for user in user_list:
            #TODO: Check credibility
            rm = RoleMapping()
            rm.parent = c
            rm.child = user

    @contest.method
    @ReturnValue(type=Contestant)
    @Argument('token', type=str)
    @Argument('contest', type=Contest)
    @Argument('user', type=User)
    def get_contestant(contest, user):
        c = Contestant().objects.filter(contest=contest).filter(children__id=user.id)[0]
        return c
