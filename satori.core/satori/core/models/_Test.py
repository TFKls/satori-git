from django.db import models
from satori.dbev import events
from satori.objects import Argument, ReturnValue
from satori.ars import django_
from satori.ars.model import String
from satori.core.models._Object import Object

class Test(Object):
    """Model. Single test.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_test')

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

class TestOpers(django_.Opers):
    test = django_.ModelProceduresProvider(Test)

