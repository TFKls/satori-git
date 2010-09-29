# vim:ts=4:sts=4:sw=4:expandtab
from django.db import transaction

from satori.core.checking import accumulators
from satori.core.checking.utils import wrap_transaction
from satori.core.models import Test, TestResult
from satori.events import Event, Client2

class SerialDispatcher(Client2):
    def __init__(self, test_suite_result, accumulator_list):
        super(serial_dispatcher, self).__init__()
        self.test_suite_result = test_suite_result
        self.queue = 'dispatcher_{0}'.format(test_suite_result.id) #TODO: are we sure, that she's the one?
        self.accumulators = [
                getattr(accumulators, accumulator)(test_suite_result) for accumulator in accumulator_list
        ]
        
    def send_test(self):
        while self.to_check:
            next_test = Test.get(id=self.to_check.popleft())
            (next_test_result, created) = TestResult.objects.get_or_create(submit=self.test_suite_result.submit, test=next_test)
            if created:
                self.next_test_result_id = next_test_result.id
                return
            else:
                for accumulator in self.accumulators:
                	accumulator.accumulate(next_test_result)
                if any(not accumulator.status() for accumulator in self.accumulators):
                    self.finish()
                    return

        self.finish()

    @wrap_transaction
    def init(self):
        self.attach(self.queue)
        self.map({'type': 'db', 'model': 'core.testresult', 'action': 'U', 'new.pending': True, 'new.submit': self.test_suite_result.submit.id}, self.queue) 

        self.next_test_result_id = -1

        self.to_check = deque()
        for test in self.test_suite_result.test_suite.tests.all():
        	self.to_check.append(test.id)

        for accumulator in self.accumulators:
            accumulator.init()

        self.send_test()

    @wrap_transaction
    def deinit(self):
        for accumulator in self.accumulators:
            accumulator.deinit()
		self.test_suite_result.pending = False
		self.test_suite_result.save()

    @wrap_transaction
    def handle_event(self, queue, event):
        if event.object_id != self.next_test_result_id:
            return

        result = TestResult.objects.get(id=event.object_id)

        for accumulator in self.accumulators:
            accumulator.accumulate(result)

        if any(not accumulator.status() for accumulator in self.accumulators):
            self.finish()
        else:
            self.send_test()


class ParalellDispatcher(Client2):
    def __init__(self, test_suite_result, accumulator_list):
        super(serial_dispatcher, self).__init__()
        self.test_suite_result = test_suite_result
        self.queue = 'dispatcher_{0}'.format(test_suite_result.id) #TODO: are we sure, that she's the one?
        self.accumulators = [
                getattr(accumulators, accumulator)(test_suite_result) for accumulator in accumulator_list
        ]
        
    @wrap_transaction
    def init(self):
        self.attach(self.queue)
        self.map({'type': 'db', 'model': 'core.testresult', 'action': 'U', 'new.pending': True, 'new.submit': self.test_suite_result.submit.id}, self.queue) 

        for accumulator in self.accumulators:
            accumulator.init()

        self.wanted_test_result_ids = set()
        for test in self.test_suite_result.test_suite.tests.all():
            (test_result, created) = TestResult.objects.get_or_create(submit=self.test_suite_result.submit, test=test)
            if created:
                self.wanted_test_result_ids.add(test_result.id)
            else:
                for accumulator in self.accumulators:
                	accumulator.accumulate(next_test_result)
#                ?
#                if any(not accumulator.status() for accumulator in self.accumulators):
#                    self.finish()
#                    return

    @wrap_transaction
    def deinit(self):
        for accumulator in self.accumulators:
            accumulator.deinit()
		self.test_suite_result.pending = False
		self.test_suite_result.save()

    @wrap_transaction
    def handle_event(self, queue, event):
        if event.object_id not in self.wanted_test_result_ids:
            return

        self.wanted_test_result_ids.remove(event.object_id)

        result = TestResult.objects.get(id=event.object_id)

        for accumulator in self.accumulators:
            accumulator.accumulate(result)

#       ?
#        if any(not accumulator.status() for accumulator in self.accumulators):
#            self.finish()
