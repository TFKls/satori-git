# vim:ts=4:sts=4:sw=4:expandtab
import logging

class AccumulatorBase(object):
    def __init__(self, test_suite_result):
        super(AccumulatorBase, self).__init__()
        self.test_suite_result = test_suite_result

    def init(self):
        pass

    def accumulate(self, test_result):
        pass

    def status(self):
        return True

    def deinit(self):
        pass


class StatusAccumulator(AccumulatorBase):
    def __init__(self, test_suite_result):
        super(StatusAccumulator, self).__init__(test_suite_result)

    def init(self):
        self._status = 'OK'
        self.test_suite_result.oa_set_str('status', 'QUE')
        self.test_suite_result.status = 'QUE'
        self.test_suite_result.save()

    def accumulate(self, test_result):
        status = test_result.oa_get_str('status')
        logging.debug('Status Accumulator %s: %s += %s', self.test_suite_result.id, self._status, status)
        if status is None:
            status = 'INT'
        if self._status == 'OK' and status != 'OK':
            self._status = status

    def status(self):
        return self._status == 'OK'

    def deinit(self):
        logging.debug('Status Accumulator %s: %s', self.test_suite_result.id, self._status)
        self.test_suite_result.oa_set_str('status', self._status)
        self.test_suite_result.status = self._status
        self.test_suite_result.save()

class CountAccumulator(AccumulatorBase):
    def __init__(self, test_suite_result):
        super(CountAccumulator, self).__init__(test_suite_result)

    def init(self):
#        print 'CountAccumulator starting up!'
        self.suite = self.test_suite_result.test_suite
#        self.testcount = self.suite.get_tests().count()
        self.checked = 0
        self.passed = 0
        self._status = '0 / 0'
        self.test_suite_result.oa_set_str('status', 'QUE')
        self.test_suite_result.status = 'QUE'
        self.test_suite_result.report = ''
        self.test_suite_result.save()

    def accumulate(self, test_result):
        status = test_result.oa_get_str('status')
        logging.debug('Status Accumulator %s: %s += %s', self.test_suite_result.id, self._status, status)
        self.test_suite_result.report = self.test_suite_result.report + ' [' + test_result.test.name + ' : ' + status + ']'
        if status is None:
            status = 'INT'
        self.checked = self.checked+1
        if status == 'OK':
            self.passed = self.passed+1
        self._status = str(self.passed) + ' / '+ str(self.checked)
        self.test_suite_result.save()

    def status(self):
        return True

    def deinit(self):
        logging.debug('Status Accumulator %s: %s', self.test_suite_result.id, self._status)
        self.test_suite_result.oa_set_str('status', self._status)
        self.test_suite_result.oa_set_str('checked', self.checked)
        self.test_suite_result.oa_set_str('passed', self.passed)
        self.test_suite_result.status = self._status
        self.test_suite_result.save()


accumulators = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, AccumulatorBase) and (item != AccumulatorBase):
        accumulators[item.__name__] = item
