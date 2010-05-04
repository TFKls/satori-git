from django.db import models
from satori.dbev import events
from satori.ars import django2ars
from satori.core.models._Object import Object

class Submit(Object):
    """Model. Single problem solution (within or outside of a Contest).
    """
    __module__ = "satori.core.models"

    owner       = models.ForeignKey('Contestant', null=True)
    problem     = models.ForeignKey('ProblemIncarnation', null=True)
    time        = models.DateTimeField(auto_now_add=True)
class SubmitEvents(events.Events):
    model = Submit
    on_insert = on_update = ['owner', 'problem']
    on_delete = []
