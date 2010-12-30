# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class TestSuiteResult(Entity):
    """Model. Result of a TestSuite for a single Submit.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_testsuiteresult')

    submit        = models.ForeignKey('Submit', related_name='test_suite_results')
    test_suite    = models.ForeignKey('TestSuite', related_name='test_suite_results+')
    pending       = models.BooleanField(default=True)
    status        = models.CharField(max_length=50)
    report        = models.TextField()

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('submit', 'test_suite'),)

    class ExportMeta(object):
        fields = [('submit', 'VIEW'), ('test_suite', 'VIEW'), ('pending', 'VIEW'), ('status', 'VIEW'), ('report', 'VIEW')]

    @ExportMethod(NoneType, [DjangoId('TestSuiteResult')], PCArg('self', 'MANAGE'))
    def rejudge(self):
        RawEvent().send(Event(type='checking_rejudge_test_suite_result', id=self.id))

class TestSuiteResultEvents(Events):
    model = TestSuiteResult
    on_insert = on_update = ['submit', 'test_suite', 'pending']
    on_delete = []
