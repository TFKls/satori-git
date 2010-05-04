from django.db import models
from satori.dbev import events
from satori.ars import django2ars
from satori.core.models._Object import Object

class TestSuiteResult(Object):
    """Model. Result of a TestSuite for a single Submit.
    """
    __module__ = "satori.core.models"

    submit      = models.ForeignKey('Submit')
    test_suite  = models.ForeignKey('TestSuite')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('submit', 'test_suite'),)

class TestSuiteResultEvents(events.Events):
    model = TestSuiteResult
    on_insert = on_update = ['submit', 'test_suite']
    on_delete = []

class TestSuiteResultOpers(django2ars.Opers):
    testsuiteresult = django2ars.ModelOpers(TestSuiteResult)

