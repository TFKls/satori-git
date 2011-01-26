# vim:ts=4:sts=4:sw=4:expandtab
import logging

class ReporterBase(object):
    def __init__(self, test_suite_result):
        super(ReporterBase, self).__init__()
        self.test_suite_result = test_suite_result

    def init(self):
        pass

    def accumulate(self, test_result):
        pass

    def status(self):
        return True

    def deinit(self):
        pass


class StatusReporter(ReporterBase):
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


class CountReporter(ReporterBase):
    def __init__(self, test_suite_result):
        super(CountReporter, self).__init__(test_suite_result)

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
        self.test_suite_result.report = self.test_suite_result.report + ' [' + test_result.test.name + ' : ' + test_result.oa_get_str('status') + ']'
        self.test_suite_result.save()

    def deinit(self):
        status = self.test_suite_result.oa_get_str('status')
        if status is None:
            status = ''
        self.test_suite_result.status = status
#        self.test_suite_result.report = 'Finished checking: {0}'.format(status)
        self.test_suite_result.save()


reporters = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, ReporterBase) and (item != ReporterBase):
        reporters[item.__name__] = item
