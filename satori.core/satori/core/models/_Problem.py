from django.db import models
from satori.dbev import events
from satori.ars import wrapper
from satori.core import cwrapper
from satori.core.models._Object import Object

class Problem(Object):
    """Model. Description of an (abstract) problems.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_problem')

    name        = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, default="")
    
    def __unicode__(self):
        return self.name+" ("+self.description+")"

class ProblemEvents(events.Events):
    model = Problem
    on_insert = on_update = ['name']
    on_delete = []

class ProblemWrapper(wrapper.WrapperClass):
    problem = cwrapper.ModelWrapper(Problem)

