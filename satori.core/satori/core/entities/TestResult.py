# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev               import Events

from satori.core.models import Entity

@ExportModel
class TestResult(Entity):
    """Model. Result of a single Test for a single Submit.
    """

    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_testresult')

    submit      = models.ForeignKey('Submit')
    test        = models.ForeignKey('Test')
    tester      = models.ForeignKey('User', null=True)
    pending     = models.BooleanField(default=True)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('submit', 'test'),)

    class ExportMeta(object):
        fields = [('submit', 'VIEW'), ('test', 'VIEW'), ('pending', 'VIEW'), ('tester', 'VIEW')]

    @ExportMethod(NoneType, [DjangoId('TestResult')], PCArg('self', 'MANAGE'))
    def rejudge(self):
        RawEvent().send(Event(type='checking_rejudge_test_result', id=self.id))


class TestResultEvents(Events):
    model = TestResult
    on_insert = on_update = ['submit', 'test', 'tester', 'pending']
    on_delete = []
