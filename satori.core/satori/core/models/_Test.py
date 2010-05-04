from django.db import models
from satori.dbev import events
from satori.ars import django2ars
from satori.core.models._Object import Object

class Test(Object):
    """Model. Single test.
    """
    __module__ = "satori.core.models"

    owner       = models.ForeignKey('User', null=True)
    problem     = models.ForeignKey('Problem', null=True)
    name        = models.CharField(max_length=50)
    description = models.TextField(blank=True, default="")
    environment = models.CharField(max_length=50)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('problem', 'name'),)
class TestEvents(events.Events):
    model = Test
    on_insert = on_update = ['owner', 'problem', 'name']
    on_delete = []
