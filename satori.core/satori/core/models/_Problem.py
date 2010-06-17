from django.db import models
from satori.dbev import events
from satori.ars import django_
from satori.core.models._Object import Object

class Problem(Object):
    """Model. Description of an (abstract) problems.
    """
    __module__ = "satori.core.models"

    name        = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, default="")

class ProblemEvents(events.Events):
    model = Problem
    on_insert = on_update = ['name']
    on_delete = []

class ProblemOpers(django_.Opers):
    problem = django_.ModelProceduresProvider(Problem)

