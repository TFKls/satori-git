from django.db import models
from satori.dbev import events
from satori.ars import django_
from satori.core.models._Object import Object

class TestResult(Object):
    """Model. Result of a single Test for a single Submit.
    """
    __module__ = "satori.core.models"

    submit      = models.ForeignKey('Submit')
    test        = models.ForeignKey('Test')
    tester      = models.ForeignKey('User')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('submit', 'test'),)

class TestResultEvents(events.Events):
    model = TestResult
    on_insert = on_update = ['submit', 'test', 'tester']
    on_delete = []

class TestResultOpers(django_.Opers):
    testresult = django_.ModelProceduresProvider(TestResult)

