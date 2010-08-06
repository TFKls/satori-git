# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._Object import Object

class Problem(Object):
    """Model. Description of an (abstract) problems.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_problem')

    name        = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, default="")
    
    def __str__(self):
        return self.name+" ("+self.description+")"

    def inherit_right(self, right):
        right = str(right)
        ret = list()
        if right == 'EDIT':
            pass
        return ret
    

class ProblemEvents(events.Events):
    model = Problem
    on_insert = on_update = ['name']
    on_delete = []

