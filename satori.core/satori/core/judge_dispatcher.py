# vim:ts=4:sts=4:sw=4:expandtab
import collections
import os
from threading import Lock
from time import sleep
from satori.events import QueueId, Attach, Map, Receive, Send, Event
from satori.core.models import TestResult
from multiprocessing.connection import Client
from satori.events import Slave
from satori.core.models import *

def judge_dispatcher():
    enqueue = QueueId('judge_dispatcher_enqueue')
    dequeue = QueueId('judge_dispatcher_dequeue')
    yield Attach(enqueue)
    yield Attach(dequeue)
    enqueue_mapping = yield Map({'type': 'judge_dispatcher_enqueue'}, enqueue)
    dequeue_mapping = yield Map({'type': 'judge_dispatcher_dequeue'}, dequeue)
    work_queue = collections.deque()
    while True:
        queue, event = yield Receive()
        if queue == enqueue:
            work_queue.append(event)
            print 'Judge dispatcher: enqueue:', event
        if queue == dequeue:
            e = Event(type='judge_dispatcher_dequeue_result')
            e.tag = event.tag
            try:
                to_test = work_queue.popleft()
            except IndexError:
                e.test_result_id = None
            else:
                tr = TestResult.objects.filter(test=Test.objects.get(id=to_test.test_id), submit=Submit.objects.get(id=to_test.submit_id))
                if tr:
                    tr = tr[0]
                else:
                    tr = TestResult(test=Test.objects.get(id=to_test.test_id), submit=Submit.objects.get(id=to_test.submit_id))
                tr.tester = User.objects.get(id=event.tester_id)
                tr.save()
                e.test_result_id = tr.id
            print 'JudgeDispatcher: dequeue by', event.tester_id, ':', e
            yield Send(e)

class JudgeDispatcherClient(object):
    _pid = -1

    @classmethod
    def get_instance(cls):
        pid = os.getpid()
        if pid != cls._pid:
        	cls._instance = JudgeDispatcherClient(pid=pid)
        	cls._pid = pid
        return cls._instance

    def __init__(self, pid):
        self.lock = Lock()
        self.lock.acquire()
        self.connection = Client(address=('localhost', 38888))
        queue = QueueId('judge_dispatcher_client_' + str(pid))
        self.connection.send(Attach(queue))
        self.connection.recv()
        self.connection.send(Map({'type': 'judge_dispatcher_dequeue_result', 'tag': str(pid)}, queue))
        self.connection.recv()
        self.lock.release()                

    def get_next(self, user):
        self.lock.acquire()
        self.connection.send(Send(Event(type='judge_dispatcher_dequeue', tag=str(self._pid), tester_id=user.id)))
        self.connection.recv()
        print 'a'
        self.connection.send(Receive())
        print 'b'
        result = self.connection.recv()
        print 'c'
        self.lock.release()
        return result[1]

def judge_generator():
    sleep(10)

    c = Contestant.objects.all()[0]
    pm = ProblemMapping.objects.all()[0]
    t = Test.objects.all()[0]
    s = Submit(contestant=c, problem=pm)
    s.save()
    yield Send(Event(type='judge_dispatcher_enqueue', test_id=t.id, submit_id=s.id))
    sleep(1)
    s = Submit(contestant=c, problem=pm)
    s.save()
    yield Send(Event(type='judge_dispatcher_enqueue', test_id=t.id, submit_id=s.id))
    sleep(30)
    s = Submit(contestant=c, problem=pm)
    s.save()
    yield Send(Event(type='judge_dispatcher_enqueue', test_id=t.id, submit_id=s.id))


