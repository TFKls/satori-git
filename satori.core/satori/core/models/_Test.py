# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._Object import Object

class Test(Object):
    """Model. Single test.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_test')

    owner       = models.ForeignKey('User')
    problem     = models.ForeignKey('Problem')
    name        = models.CharField(max_length=50)
    description = models.TextField(blank=True, default="")
    environment = models.CharField(max_length=50)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('problem', 'name'),)

class TestEvents(events.Events):
    model = Test
    on_insert = on_update = ['owner', 'problem', 'name']
    on_delete = []

