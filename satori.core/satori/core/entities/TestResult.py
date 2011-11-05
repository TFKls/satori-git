# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class TestResult(Entity):
    """Model. Result of a single Test for a single Submit.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_testresult')

    submit        = models.ForeignKey('Submit', related_name='test_results', on_delete=models.CASCADE)
    test          = models.ForeignKey('Test', related_name='test_results', on_delete=models.CASCADE)
    tester        = models.ForeignKey('Role', related_name='test_results+', null=True, on_delete=models.SET_NULL)
    pending       = models.BooleanField(default=True)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('submit', 'test'),)

    class ExportMeta(object):
        fields = [('submit', 'VIEW'), ('test', 'VIEW'), ('pending', 'VIEW')]

    class RightsMeta(object):
        inherit_parent = 'submit'
        inherit_parent_require = 'VIEW'

        inherit_parent_MANAGE = ['MANAGE']

    @classmethod
    def inherit_rights(cls):
        inherits = super(TestResult, cls).inherit_rights()
        cls._inherit_add(inherits, 'MANAGE', 'submit', 'MANAGE')
        return inherits

    @ExportMethod(NoneType, [DjangoId('TestResult')], PCArg('self', 'MANAGE'))
    def rejudge(self):
        RawEvent().send(Event(type='checking_rejudge_test_result', id=self.id))

class TestResultEvents(Events):
    model = TestResult
    on_insert = on_update = ['submit', 'test', 'tester', 'pending']
    on_delete = []
