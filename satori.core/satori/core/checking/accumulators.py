# vim:ts=4:sts=4:sw=4:expandtab

class StatusAccumulator(object):
    def __init__(self, test_suite_result):
        super(StatusAccumulator, self).__init__()
        self.test_suite_result = test_suite_result

    def init(self):
        self._status = 'OK'

    def accumulate(self, test_result):
        status = test_result.attributes.oa_get_str('status')
        print 'Default Status Accumulator', self.test_suite_result.id, ':', self._status, '+=', status
        if status is None:
            status = 'INT'
        if self._status == 'OK' and status != 'OK':
            self._status = status

    def status(self):
        return self._status == 'OK'

    def deinit(self):
        print 'Default Status Accumulator', self.test_suite_result.id, ':', self._status, '?'
        self.test_suite_result.attributes.oa_set_str('status', self._status)
