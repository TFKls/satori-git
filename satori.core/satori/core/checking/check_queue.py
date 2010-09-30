# vim:ts=4:sts=4:sw=4:expandtab
from collections import deque
import traceback
from satori.core.models import TestResult
from satori.core.checking.utils import wrap_transaction
from satori.events import Event, Client2

class CheckQueue(Client2):
    queue = 'check_queue_queue'

    def __init__(self):
        super(CheckQueue, self).__init__()
        self.work_queue = deque()
        self.work_set = set()

    def append(self, id):
        if id not in self.work_set:
            self.work_queue.append(id)
            self.work_set.add(id)

    def pop(self):
        try:
            id = self.work_queue.popleft()
        except IndexError:
            return None
        self.work_set.remove(id)
        return id

    @wrap_transaction
    def init(self):
        for test_result in TestResult.objects.filter(pending=True):
            self.append(test_result.id)
        self.attach(self.queue)
        self.map({'type': 'db', 'model': 'core.testresult', 'action': 'I'}, self.queue)
        self.map({'type': 'check_queue_dequeue'}, self.queue)
        self.map({'type': 'testresult_reschedule'}, self.queue)

    @wrap_transaction
    def handle_event(self, queue, event):
        if event.type == 'db':
            self.append(event.object_id)
            print 'Check queue: enqueue:', event
        elif event.type == 'testresult_reschedule':
            self.append(event.test_result_id)
            print 'Check queue: reschedule:', event
        elif event.type == 'check_queue_dequeue':
            e = Event(type='check_queue_dequeue_result')
            e.tag = event.tag
            e.test_result_id = self.pop()
            if not e.test_result_id is None:
                tr = TestResult.objects.get(id=e.test_result_id)
                tr.tester = User.objects.get(id=event.tester_id)
                tr.save()
            print 'Check queue: dequeue by', event.tester_id, ':', e
            self.send(e)
