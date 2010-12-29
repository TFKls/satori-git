# vim:ts=4:sts=4:sw=4:expandtab
import logging
from collections import deque

from satori.core.checking.accumulators import accumulators
from satori.core.models import Test

class DispatcherBase(object):
    def __init__(self, supervisor, test_suite_result, accumulator_list = []):
        super(DispatcherBase, self).__init__()
        self.supervisor = supervisor
        self.test_suite_result = test_suite_result
        self.accumulators = [
            accumulators[accumulator](test_suite_result) for accumulator in accumulator_list
        ]
        for accumulator in self.accumulators:
            accumulator.init()
    def checked_test_result(self, test_results):
        raise NotImplementedError
    def rejudge_test_result(self, test_results):
        raise NotImplementedError
    def changed_overrides(self):
        raise NotImplementedError

    def accumulate(self, test_result):
        for accumulator in self.accumulators:
            accumulator.accumulate(test_result)

    def status(self):
        return all(accumulator.status() for accumulator in self.accumulators)

    def finish(self):
        for accumulator in self.accumulators:
            accumulator.deinit()
        self.supervisor.finished_test_suite_result()

class SerialDispatcher(DispatcherBase):
    """Serial dispatcher"""

    def __init__(self, supervisor, test_suite_result, accumulator_list = []):
        super(SerialDispatcher, self).__init__(supervisor, test_suite_result, accumulator_list)
        self.to_check = deque()
        for test in self.test_suite_result.test_suite.tests.all():
            self.to_check.append(test.id)
        self.send_test()

    def checked_test_result(self, test_results):
        for result in test_results:
            assert result.id == self.to_check[0]
            self.to_check.popleft()
            self.accumulate(result)
            if not self.status():
                self.finish()
        self.send_test()

    def send_test(self):
        if self.to_check:
            submit = test_suite_result.submit
            test = Test.objects.get(id=self.to_check[0])
            self.supervisor.schedule_test_result(test_suite_result=self.test_suite_result, submit=submit, test=test)
        else:
            self.finish()

class ParallelDispatcher(DispatcherBase):
    """Parallel dispatcher"""

    def __init__(self, supervisor, test_suite_result, accumulator_list = []):
        super(ParallelDispatcher, self).__init__(supervisor, test_suite_result, accumulator_list)
        submit = test_suite_result.submit
        self.to_check = set()
        for test in self.test_suite_result.test_suite.tests.all():
            self.to_check.add(test.id)
            self.supervisor.schedule_test_result(test_suite_result=self.test_suite_result, submit=submit, test=test)

    def checked_test_result(self, test_results):
        for result in test_results:
            assert result.id in self.to_check
            self.to_check.remove(result.id)
            self.accumulate(result)
            if not self.status():
                self.finish()
        if not self.to_check:
            self.finish()

dispatchers = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, DispatcherBase) and (item != DispatcherBase):
        dispatchers[item.__name__] = item
