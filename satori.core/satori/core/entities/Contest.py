# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models
from satori.dbev import Events
from satori.core.models import Entity
from satori.core.models import AttributeGroup

class Contest(Entity):
    """Model. Description of a contest.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Entity, parent_link=True, related_name='cast_contest')

    name        = models.CharField(max_length=50, unique=True)
    problems    = models.ManyToManyField('Problem', through='ProblemMapping')
    files       = models.OneToOneField('AttributeGroup', related_name='group_contest_files')
    contestant_role = models.ForeignKey('Role')

    def save(self):
        try:
            x = self.files
        except AttributeGroup.DoesNotExist:
            files = AttributeGroup()
            files.save()
            self.files = files

        super(Contest, self).save()

    def __str__(self):
        return self.name
    # TODO: add presentation options

    def inherit_right(self, right):
        right = str(right)
        ret = super(Contest, self).inherit_right(right)
        if right == 'VIEW' or right == 'OBSERVE' or right == 'VIEWTASKS':
            ret.append((self,'MANAGE'))
        if right == 'APPLY':
            ret.append((self,'JOIN'))
        return ret



class ContestEvents(Events):
    model = Contest
    on_insert = on_update = ['name']
    on_delete = []

#! module api

from satori.objects import Argument, ReturnValue
from satori.ars.wrapper import TypedList, WrapperClass
from satori.core.cwrapper import ModelWrapper
from satori.core.models import *
from satori.core.sec import Token

class ApiContest(WrapperClass):
    contest = ModelWrapper(Contest)

    contest.attributes('files')

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
        Privilege.grant(token.user, c, 'MANAGE')
        Privilege.grant(r, c, 'VIEW')
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
        RoleMapping(parent = self.contestant_role, child = contestant).save()
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
        contestant = Contestant.objects.get(contest=self, children__id=token.user.id)
        if problem_mapping.contest != self:
            raise "Go away"
        submit = Submit()
        submit.contestant = contestant
        submit.problem = problem_mapping
        submit.save()
        Privilege.grant(contestant, submit, 'VIEW')
        blob = OpenAttribute.create_blob()
        blob.write(content)
        hash = blob.close()
        submit.data.attributes.oa_set_blob_hash(name='content', hash=hash, filename=filename)
        TestSuiteResult(submit=submit, test_suite=problem_mapping.default_test_suite).save()
        return submit
    @contest.submit.can
    def submit_check(token, self, problem_mapping, content, filename):
        return problem_mapping.demand_right(token, 'SUBMIT')

