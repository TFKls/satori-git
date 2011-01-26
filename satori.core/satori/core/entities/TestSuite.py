# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Entity

@ExportModel
class TestSuite(Entity):
    """Model. A group of tests, with dispatch and aggregation algorithm.
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_testsuite')

    problem       = models.ForeignKey('Problem', related_name='test_suites')
    name          = models.CharField(max_length=50)
    description   = models.TextField(blank=True, default="")
    tests         = models.ManyToManyField('Test', through='TestMapping', related_name='test_suites')
    dispatcher    = models.CharField(max_length=128)
    reporter      = models.CharField(max_length=128)
    accumulators  = models.CharField(max_length=1024)

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('problem', 'name'),)

    class ExportMeta(object):
        fields = [('problem', 'VIEW'), ('name', 'VIEW'), ('description', 'VIEW'), ('dispatcher', 'VIEW'), ('accumulators', 'VIEW'), ('reporter', 'VIEW')]

    @classmethod
    def inherit_rights(cls):
        inherits = super(TestSuite, cls).inherit_rights()
        cls._inherit_add(inherits, 'MANAGE', 'problem', 'EDIT')
        return inherits

    def save(self, *args, **kwargs):
        from satori.core.checking.dispatchers  import dispatchers
        from satori.core.checking.accumulators import accumulators
        from satori.core.checking.reporters import reporters
        if not self.dispatcher in dispatchers:
            raise ValueError('Dispatcher '+self.dispatcher+' is not allowed')
        if not self.reporter in reporters:
            raise ValueError('Reporter '+self.reporter+' is not allowed')
        for accumulator in self.accumulators.split(','):
            if not accumulator in accumulators:
                raise ValueError('Accumulator '+accumulator+' is not allowed')
        super(TestSuite,self).save(*args, **kwargs)

    @ExportMethod(DjangoStruct('TestSuite'), [DjangoStruct('TestSuite'), DjangoIdList('Test')], PCArgField('fields', 'problem', 'MANAGE'), [CannotSetField])
    @staticmethod
    def create(fields, test_list):
        test_suite = TestSuite()
        test_suite.forbid_fields(fields, ['id'])
        test_suite.update_fields(fields, ['problem', 'name', 'description', 'dispatcher', 'reporter', 'accumulators'])
        test_suite.save()
        count = 0
        for test in test_list:
            count += 1
            TestMapping(suite=test_suite, test=test, order=count).save()
        return test_suite

    @ExportMethod(DjangoStruct('TestSuite'), [DjangoId('TestSuite'), DjangoStruct('TestSuite')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, ['id', 'problem', 'dispatcher', 'reporter', 'accumulators'])
        self.update_fields(fields, ['name', 'description'])
        return self

    @ExportMethod(DjangoStruct('TestSuite'), [DjangoId('TestSuite'), DjangoStruct('TestSuite'), DjangoIdList('Test')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify_full(self, fields, test_list):
        self.forbid_fields(fields, ['id', 'problem'])
        self.update_fields(fields, ['name', 'description', 'dispatcher', 'reporter', 'accumulators'])
        self.save()
        TestMapping.objects.filter(suite=self).delete()
        count = 0
        for test in test_list:
            count += 1
            TestMapping(suite=self, test=test, order=count).save()
        self.rejudge()
        return self

    @ExportMethod(DjangoStructList('Test'), [DjangoId('TestSuite')], PCArg('self', 'MANAGE'))
    def get_tests(self):
        return self.tests.all().extra(order_by=['core_testmapping.order'])

    @ExportMethod(NoneType, [DjangoId('TestSuite')], PCArg('self', 'MANAGE'))
    def rejudge(self):
        RawEvent().send(Event(type='checking_rejudge_test_suite', id=self.id))

class TestSuiteEvents(Events):
    model = TestSuite
    on_insert = on_update = ['owner', 'problem', 'name']
    on_delete = []
