# vim:ts=4:sts=4:sw=4:expandtab
import collections
import os
from threading import Lock
from time import sleep
import satori.core.setup
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
        self.connection = Client(address=(satori.core.setup.settings.EVENT_HOST, satori.core.setup.settings.EVENT_PORT))
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

    def set_result(self, result):
        self.lock.acquire()
        self.connection.send(Send(Event(type='judge_dispatcher_finished', submit_id=result.submit.id, test_id=result.test.id, test_result_id=result.id)))
        self.lock.release()

def judge_generator(slave):
    qid = QueueId('new_submits')
    yield Attach(qid)
    yield Map({'type': 'db', 'model': 'core_submit'}, qid)

    while True:
        queue, event = yield Receive()
        if queue == qid:
        	sub = Submit.objects.get(id=event.object_id)
        	suite = sub.problem.default_test_suite
            (dispatcher_module, dispatcher_func) = suite.dispatcher.rsplit('.',1)
            dispatcher_module = __import__(dispatcher_module, globals(), locals(), [ dispatcher_func ], -1)
            dispatcher = getattr(dispatcher_module, dispatcher_func)
            slave.schedule(dispatcher(sub, suite))


def default_serial_dispatcher(submit, suite):
    qid = QueueId('dispatcher_' + '_'.join([str(x) for x in [submit.id, suite.id]]))
    yield Attach(qid)
    yield Map({'type': 'judge_dispatcher_finished', 'submit_id': submit.id}, qid)
    for test in suite.tests:
        try:
        	result = TestResult.objects.get(submit=submit, test=test)
        except:
            yield Send(Event(type='judge_dispatcher_enqueue', test_id=test.id, submit_id=submit.id))
            while True:
        	    queue, event = yield Receive()
                if queue == qid and event.test_id == test.id and event.submit_id == submit.id:
                	result = TestResult.objects.get(id=event.test_result_id)
                	break
        #TODO: Group results
        pass
