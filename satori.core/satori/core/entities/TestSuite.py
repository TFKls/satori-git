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
    
    params        = AttributeGroupField(PCArg('self', 'MANAGE'), PCDeny(), '')

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
        self.fixup_params()
        from satori.core.checking.dispatchers  import dispatchers
        from satori.core.checking.accumulators import accumulators
        from satori.core.checking.reporters import reporters
        if not self.dispatcher in dispatchers:
            raise ValueError('Dispatcher '+self.dispatcher+' is not allowed')
        if not self.reporter in reporters:
            raise ValueError('Reporter '+self.reporter+' is not allowed')
        if self.accumulators:
            for accumulator in self.accumulators.split(','):
                if not accumulator in accumulators:
                    raise ValueError('Accumulator '+accumulator+' is not allowed')
        super(TestSuite,self).save(*args, **kwargs)

    @ExportMethod(DjangoStruct('TestSuite'), [DjangoStruct('TestSuite'), TypedMap(unicode, AnonymousAttribute), DjangoIdList('Test'), TypedList(TypedMap(unicode, AnonymousAttribute))],
        PCAnd(PCArgField('fields', 'problem', 'MANAGE'), PCEachValue('params', PCRawBlob('item')), PCEach('test_params', PCEachValue('item', PCRawBlob('item')))),
        [CannotSetField])
    @staticmethod
    def create(fields, params, test_list, test_params):
        if len(test_list) != len(test_params):
            raise RuntimeError('Bad test_params length.')
        test_suite = TestSuite()
        test_suite.forbid_fields(fields, ['id'])
        test_suite.update_fields(fields, ['problem', 'name', 'description', 'dispatcher', 'reporter', 'accumulators'])
        test_suite.save()
        test_suite.params_set_map(params)
        count = 0
        for test in test_list:
            t = TestMapping(suite=test_suite, test=test, order=count)
            t.save()
            t.params_set_map(test_params[count])
            count += 1
        return test_suite

    @ExportMethod(DjangoStruct('TestSuite'), [DjangoId('TestSuite'), DjangoStruct('TestSuite')], PCArg('self', 'MANAGE'), [CannotSetField])
    def modify(self, fields):
        self.forbid_fields(fields, ['id', 'problem', 'dispatcher', 'reporter', 'accumulators'])
        self.update_fields(fields, ['name', 'description'])
        return self

    @ExportMethod(DjangoStruct('TestSuite'), [DjangoId('TestSuite'), DjangoStruct('TestSuite'), 
        TypedMap(unicode, AnonymousAttribute), DjangoIdList('Test'), TypedList(TypedMap(unicode, AnonymousAttribute))],
        PCAnd(PCArg('self', 'MANAGE'), PCEachValue('params', PCRawBlob('item')), PCEach('test_params', PCEachValue('item', PCRawBlob('item')))),
        [CannotSetField])
    def modify_full(self, fields, params, test_list, test_params):
        if len(test_list) != len(test_params):
            raise RuntimeError('Bad test_params length.')
        self.forbid_fields(fields, ['id', 'problem'])
        self.update_fields(fields, ['name', 'description', 'dispatcher', 'reporter', 'accumulators'])
        self.save()
        self.params_set_map(params)
        TestMapping.objects.filter(suite=self).delete()
        count = 0
        for test in test_list:
            t = TestMapping(suite=self, test=test, order=count)
            t.save()
            t.params_set_map(test_params[count])
            count += 1
        self.rejudge()
        return self

    @ExportMethod(DjangoStructList('Test'), [DjangoId('TestSuite')], PCArg('self', 'MANAGE'))
    def get_tests(self):
        return self.tests.all().extra(order_by=['core_testmapping.order'])

    @ExportMethod(TypedList(TypedMap(unicode, AnonymousAttribute)), [DjangoId('TestSuite')], PCArg('self', 'MANAGE'))
    def get_test_params(self):
        return [x.params_get_map() for x in self.tests.all().extra(order_by=['core_testmapping.order'])]

    @ExportMethod(NoneType, [DjangoId('TestSuite')], PCArg('self', 'MANAGE'))
    def rejudge(self):
        RawEvent().send(Event(type='checking_rejudge_test_suite', id=self.id))

class TestSuiteEvents(Events):
    model = TestSuite
    on_insert = on_update = ['owner', 'problem', 'name']
    on_delete = []
