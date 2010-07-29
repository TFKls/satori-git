from django.db import models
from satori.dbev import events
from satori.ars import wrapper
from satori.core import cwrapper
from satori.core.models._Object import Object

class TestResult(Object):
    """Model. Result of a single Test for a single Submit.
    """
    __module__ = "satori.core.models"
    parent_object = models.OneToOneField(Object, parent_link=True, related_name='cast_testresult')

    submit      = models.ForeignKey('Submit')
    test        = models.ForeignKey('Test')
    tester      = models.ForeignKey('User')

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('submit', 'test'),)

class TestResultEvents(events.Events):
    model = TestResult
    on_insert = on_update = ['submit', 'test', 'tester']
    on_delete = []

class TestResultWrapper(wrapper.WrapperClass):
    testresult = cwrapper.ModelWrapper(TestResult)

