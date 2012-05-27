# vim:ts=4:sts=4:sw=4:expandtab
import logging
from collections import deque

from satori.core.checking.accumulators import accumulators
from satori.core.checking.reporters import reporters
from satori.core.models import Test, TestMapping

class DispatcherBase(object):
    def __init__(self, supervisor, test_suite_result):
        super(DispatcherBase, self).__init__()
        self.supervisor = supervisor
        self.test_suite_result = test_suite_result
        if test_suite_result.test_suite.accumulators:
            accumulator_list = test_suite_result.test_suite.accumulators.split(',')
        else:
            accumulator_list = []
        self.accumulators = [
            accumulators[accumulator](test_suite_result) for accumulator in accumulator_list
        ]
        self.reporter = reporters[test_suite_result.test_suite.reporter](test_suite_result)

    def init(self):
        for accumulator in self.accumulators:
            accumulator.init()
        self.reporter.init()

    def checked_test_results(self, test_results):
        raise NotImplementedError

    def accumulate(self, test_result):
        for accumulator in self.accumulators:
            accumulator.accumulate(test_result)
        self.reporter.accumulate(test_result)

    def status(self):
        return all(accumulator.status() for accumulator in self.accumulators) and self.reporter.status()

    def finish(self):
        for accumulator in self.accumulators:
            accumulator.deinit()
        self.reporter.deinit()
        self.supervisor.finished_test_suite_result(self.test_suite_result)

class SerialDispatcher(DispatcherBase):
    """Serial dispatcher"""

    def __init__(self, supervisor, test_suite_result):
        super(SerialDispatcher, self).__init__(supervisor, test_suite_result)
        self.to_check = deque()

    def init(self):
        super(SerialDispatcher, self).init()
        for test in self.test_suite_result.test_suite.get_tests():
            self.to_check.append(test)
        self.send_test()

    def checked_test_results(self, test_results):
        for result in test_results:
            assert result.test_id == self.to_check[0].id
            self.to_check.popleft()
            self.accumulate(result)
            if not self.status():
                self.finish()
                return
        self.send_test()

    def send_test(self):
        if self.to_check:
            submit = self.test_suite_result.submit
            test = self.to_check[0]
            self.supervisor.schedule_test_result(test_suite_result=self.test_suite_result, submit=submit, test=test)
        else:
            self.finish()

class ParallelDispatcher(DispatcherBase):
    """Parallel dispatcher"""

    def __init__(self, supervisor, test_suite_result):
        super(ParallelDispatcher, self).__init__(supervisor, test_suite_result)
        self.to_check_id = set()

    def init(self):
        super(ParallelDispatcher, self).init()
        submit = self.test_suite_result.submit
        for test in self.test_suite_result.test_suite.get_tests():
            self.to_check_id.add(test.id)
            self.supervisor.schedule_test_result(test_suite_result=self.test_suite_result, submit=submit, test=test)
        if not self.to_check_id:
            self.finish()

    def checked_test_results(self, test_results):
        for result in test_results:
            assert result.test_id in self.to_check_id
            self.to_check_id.remove(result.test_id)
            self.accumulate(result)
            if not self.status():
                self.finish()
        if not self.to_check_id:
            self.finish()

dispatchers = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, DispatcherBase) and (item != DispatcherBase):
        dispatchers[item.__name__] = item
