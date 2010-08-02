# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import events
from satori.core.models._Object import Object

class TestSuiteResult(Object):
    """Model. Result of a TestSuite for a single Submit.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_testsuiteresult')

    submit      = models.ForeignKey('Submit')
    test_suite  = models.ForeignKey('TestSuite')
    pending     = models.BooleanField(default=True)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('submit', 'test_suite'),)

class TestSuiteResultEvents(events.Events):
    model = TestSuiteResult
    on_insert = on_update = ['submit', 'test_suite']
    on_delete = []
