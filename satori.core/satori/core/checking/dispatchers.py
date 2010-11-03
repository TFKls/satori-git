# vim:ts=4:sts=4:sw=4:expandtab
from django.db import transaction
from collections import deque
import traceback

from satori.core.checking.accumulators import accumulators
from satori.core.checking.utils import wrap_transaction_management
from satori.core.models import Test, TestResult
from satori.events import Event, Client2

class DispatcherBase(Client2):
    def __init__(self, test_suite_result, accumulator_list, runner): 
        super(DispatcherBase, self).__init__()
        self.test_suite_result = test_suite_result
        self.runner = runner
        self.accumulators = [
                accumulators[accumulator](test_suite_result) for accumulator in accumulator_list
        ]

    def accumulate(self, test_result):
        for accumulator in self.accumulators:
            accumulator.accumulate(test_result)

    def status(self):
        return all(accumulator.status() for accumulator in self.accumulators)

    def do_init(self):
        self.error = False
        self.queue = 'dispatcher_{0}'.format(self.test_suite_result.id)
        self.attach(self.queue)
        self.map({'type': 'db', 'model': 'core.testresult', 'action': 'U', 'new.pending': False, 'new.submit': self.test_suite_result.submit.id}, self.queue)

        for accumulator in self.accumulators:
            accumulator.init()

    def do_deinit(self):
        for accumulator in self.accumulators:
            accumulator.deinit()

        self.test_suite_result.pending = False
        self.test_suite_result.save()

    def do_handle_event(self, queue, event):
        pass
    
    @wrap_transaction_management
    def init(self):
        try:
            self.do_init()
            transaction.commit()
        except:
            print 'Dispatcher failed'
            traceback.print_exc()
            self.error = True
            self.finish()
            transaction.rollback()

    @wrap_transaction_management
    def deinit(self):
        if not self.error:
            try:
                self.do_deinit()
                transaction.commit()
            except:
                print 'Dispatcher failed'
                traceback.print_exc()
                self.error = True
                transaction.rollback()
        if self.error:
            try:
                self.test_suite_result.oa_set_str('status', 'INT')
                self.test_suite_result.status = 'INT'
                self.test_suite_result.report = 'Internal error'
                self.test_suite_result.pending = False
                self.test_suite_result.save()
                transaction.commit()
            except:
                print 'Dispatcher error handler failed'
                traceback.print_exc()
                transaction.rollback()
        self.runner.dispatcher_stopped(self.test_suite_result)

    @wrap_transaction_management
    def handle_event(self, queue, event):
        try:
            self.do_handle_event(queue, event)
            transaction.commit()
        except:
            print 'Dispatcher failed'
            traceback.print_exc()
            self.error = True
            self.finish()
            transaction.rollback()


class SerialDispatcher(DispatcherBase):
    """Serial dispatcher"""

    def __init__(self, test_suite_result, accumulator_list, runner):
        super(SerialDispatcher, self).__init__(test_suite_result, accumulator_list, runner)

    def send_test(self):
        while self.to_check:
            next_test = Test.objects.get(id=self.to_check.popleft())
            (next_test_result, created) = TestResult.objects.get_or_create(submit=self.test_suite_result.submit, test=next_test)
            if next_test_result.pending:
                self.next_test_result_id = next_test_result.id
                return
            else:
                self.accumulate(next_test_result)
                if not self.status():
                    self.finish()
                    return

        self.finish()

    def do_init(self):
        super(SerialDispatcher, self).do_init()

        self.next_test_result_id = -1

        self.to_check = deque()
        for test in self.test_suite_result.test_suite.tests.all():
            self.to_check.append(test.id)

        self.send_test()

    def do_deinit(self):
        super(SerialDispatcher, self).do_deinit()

    def do_handle_event(self, queue, event):
        if event.object_id != self.next_test_result_id:
            return

        test_result = TestResult.objects.get(id=event.object_id)
        self.accumulate(test_result)

        if not self.status():
            self.finish()
        else:
            self.send_test()


class ParallelDispatcher(DispatcherBase):
    """Parallel dispatcher"""

    def __init__(self, test_suite_result, accumulator_list, runner):
        super(ParallelDispatcher, self).__init__(test_suite_result, accumulator_list, runner)

    def do_init(self):
        super(ParallelDispatcher, self).do_init()

        self.wanted_test_result_ids = set()
        for test in self.test_suite_result.test_suite.tests.all():
            (test_result, created) = TestResult.objects.get_or_create(submit=self.test_suite_result.submit, test=test)
            if test_result.pending:
                self.wanted_test_result_ids.add(test_result.id)
            else:
                self.accumulate(test_result)

        if not self.wanted_test_result_ids:
            self.finish()

    def do_deinit(self):
        super(ParallelDispatcher, self).do_deinit()

    def do_handle_event(self, queue, event):
        if event.object_id not in self.wanted_test_result_ids:
            return

        self.wanted_test_result_ids.remove(event.object_id)

        test_result = TestResult.objects.get(id=event.object_id)
        self.accumulate(test_result)

        if not self.wanted_test_result_ids:
            self.finish()

dispatchers = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, DispatcherBase) and (item != DispatcherBase):
        dispatchers[item.__name__] = item
