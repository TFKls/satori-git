# vim:ts=4:sts=4:sw=4:expandtab
import logging
from satori.core.models import TestSuiteResult
from satori.core.checking.dispatchers import dispatchers
from satori.core.checking.utils import wrap_transaction
from satori.events import Event, Client2

class DispatcherRunner(Client2):
    queue = 'dispatcher_runner_queue'

    def start_dispatcher(self, id):
        res = TestSuiteResult.objects.get(id=id)
        logging.debug('Dispatcher runner: starting new dispatcher %s for test suite result %s', res.test_suite.dispatcher, id)
        dispatcher = dispatchers[res.test_suite.dispatcher]
        accumulators = res.test_suite.accumulators.split(',')
        self.slave.add_client(dispatcher(res, accumulators, self))

    def dispatcher_stopped(self, test_suite_result):
        pass

    @wrap_transaction
    def init(self):
        for test_suite_result in TestSuiteResult.objects.filter(pending=True):
            self.start_dispatcher(test_suite_result.id)
        self.attach(self.queue)
        self.map({'type': 'db', 'model': 'core.testsuiteresult', 'action': 'I'}, self.queue)
        self.map({'type': 'testsuiteresult_reschedule'}, self.queue)

    @wrap_transaction
    def handle_event(self, queue, event):
        if event.type == 'db':
            self.start_dispatcher(event.object_id)
        elif event.type == 'testsuiteresult_reschedule':
            self.start_dispatcher(event.test_suite_result_id)

