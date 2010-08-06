# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._Object import Object

class Contest(Object):
    """Model. Description of a contest.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_contest')
    
    name        = models.CharField(max_length=50, unique=True)
    problems    = models.ManyToManyField('Problem', through='ProblemMapping')
    contestant_role = models.ForeignKey('Role')

    def __str__(self):
        return self.name
    # TODO: add presentation options

    def inherit_right(self, right):
        right = str(right)
        ret = list()
        if right == 'VIEW' or right == 'OBSERVE' or right == 'VIEWTASKS':
            ret.append((self,'MANAGE'))
        if right == 'APPLY':
            ret.append((self,'JOIN'))
        return ret
    

    
class ContestEvents(events.Events):
    model = Contest
    on_insert = on_update = ['name']
    on_delete = []

