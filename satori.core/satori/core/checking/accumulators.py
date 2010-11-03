# vim:ts=4:sts=4:sw=4:expandtab

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


class StatusReporter(AccumulatorBase):
    def __init__(self, test_suite_result):
        super(StatusReporter, self).__init__(test_suite_result)

    def init(self):
        status = self.test_suite_result.oa_get_str('status')
        if status is None:
            status = ''
        self.test_suite_result.status = status
        self.test_suite_result.report = ''
        self.test_suite_result.save()

    def accumulate(self, test_result):
        status = self.test_suite_result.oa_get_str('status')
        if status is None:
            status = ''
        self.test_suite_result.status = status
        self.test_suite_result.report = ''
        self.test_suite_result.save()

    def deinit(self):
        status = self.test_suite_result.oa_get_str('status')
        if status is None:
            status = ''
        self.test_suite_result.status = status
        self.test_suite_result.report = 'Finished checking: {0}'.format(status)
        self.test_suite_result.save()


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
        print 'Default Status Accumulator', self.test_suite_result.id, ':', self._status, '+=', status
        if status is None:
            status = 'INT'
        if self._status == 'OK' and status != 'OK':
            self._status = status

    def status(self):
        return self._status == 'OK'

    def deinit(self):
        print 'Default Status Accumulator', self.test_suite_result.id, ':', self._status, '?'
        self.test_suite_result.oa_set_str('status', self._status)
        self.test_suite_result.status = self._status
        self.test_suite_result.save()

accumulators = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, AccumulatorBase) and (item != AccumulatorBase):
        accumulators[item.__name__] = item
