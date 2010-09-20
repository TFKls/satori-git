# vim:ts=4:sts=4:sw=4:expandtab
from collections import deque
import os
from django.db import transaction
from threading import Lock
from time import sleep
import satori.core.setup
from satori.events import Event, Client2
from satori.core.models import TestResult
from multiprocessing.connection import Client
from satori.events import Slave, Attach, Map, Send, Receive
from satori.core.models import *

class JudgeDispatcher(Client2):
    queue_enqueue = 'judge_dispatcher_enqueue'
    queue_dequeue = 'judge_dispatcher_dequeue'

    def _init(self):
        self.work_queue = deque()
        self.attach(self.queue_enqueue)
        self.attach(self.queue_dequeue)
        self.map({'type': 'judge_dispatcher_enqueue'}, self.queue_enqueue)
        self.map({'type': 'judge_dispatcher_dequeue'}, self.queue_dequeue)

    def handle_event(self, queue, event):
        if queue == self.queue_enqueue:
            self.work_queue.append(event)
            print 'Judge dispatcher: enqueue:', event
        if queue == self.queue_dequeue:
            e = Event(type='judge_dispatcher_dequeue_result')
            e.tag = event.tag
            try:
                to_test = self.work_queue.popleft()
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
            self.send(e)

class JudgeGenerator(Client2):
    queue = 'judge_generator_new_submits'

    def _init(self):
        self.attach(self.queue)
        self.map({'type': 'db', 'model': 'core.submit', 'action': 'I'}, self.queue)

    def handle_event(self, queue, event):
        if queue == self.queue:
        	transaction.enter_transaction_management()
        	transaction.managed(True)

        	print 'OID', event.object_id
        	sub = Submit.objects.get(id=event.object_id)
        	suite = sub.problem.default_test_suite
            (dispatcher_module, dispatcher_func) = suite.dispatcher.rsplit('.',1)
            dispatcher_module = __import__(dispatcher_module, globals(), locals(), [ dispatcher_func ], -1)
            dispatcher = getattr(dispatcher_module, dispatcher_func)
            self.slave.add_client(dispatcher(sub, suite))

            transaction.commit()
            transaction.leave_transaction_management()

class default_serial_dispatcher(Client2):
    def __init__(self, submit, suite):
        super(default_serial_dispatcher, self).__init__()

        self.submit_id = submit.id
        self.suite_id = suite.id


    def _init(self):
        self.queue = 'dispatcher_' + '_'.join([str(x) for x in [self.submit_id, self.suite_id]])
        self.attach(self.queue)
        self.map({'type': 'judge_dispatcher_finished', 'submit_id': self.submit_id}, self.queue)

        self.to_check = deque()
        for test in TestSuite.objects.get(id=self.suite_id).tests.all():
        	self.to_check.append(test.id)

        self.send_test()
        
    def send_test(self):
        while self.to_check:
        	next = self.to_check.popleft()
            try:
                result = TestResult.objects.get(submit__id=self.submit_id, test__id=next)
            #TODO: except concrete exception
            except:
                self.send(Event(type='judge_dispatcher_enqueue', test_id=next, submit_id=self.submit_id))
                return

        self.finish()

    def handle_event(self, queue, event):
        self.send_test()

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
        queue = 'judge_dispatcher_client_' + str(pid)
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
        self.connection.recv()
        self.lock.release()


