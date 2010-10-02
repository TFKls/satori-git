# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import Events
from satori.core.models._Entity import Entity

class TestSuiteResult(Entity):
    """Model. Result of a TestSuite for a single Submit.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Entity, parent_link=True, related_name='cast_testsuiteresult')

    submit      = models.ForeignKey('Submit')
    test_suite  = models.ForeignKey('TestSuite')
    pending     = models.BooleanField(default=True)
    status      = models.CharField(max_length=50)
    report      = models.TextField()

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('submit', 'test_suite'),)

class TestSuiteResultEvents(Events):
    model = TestSuiteResult
    on_insert = on_update = ['submit', 'test_suite', 'pending']
    on_delete = []
