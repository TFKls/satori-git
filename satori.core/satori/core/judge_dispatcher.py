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
import traceback

class JudgeDispatcher(Client2):
    queue = 'judge_dispatcher_queue'
    
    def __init__(self):
        super(JudgeDispatcher, self).__init__()
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

    def _init(self):
        for test_result in TestResult.objects.filter(pending=True):
        	self.append(test_result.id)
        self.attach(self.queue)
        self.map({'type': 'db', 'model': 'core.testresult', 'action': 'I'}, self.queue)
        self.map({'type': 'judge_dispatcher_dequeue'}, self.queue)
        self.map({'type': 'judge_dispatcher_reschedule'}, self.queue)

    def handle_event(self, queue, event):
        if event.type == 'db':
            self.append(event.object_id)
            print 'Judge dispatcher: enqueue:', event
        elif event.type == 'judge_dispatcher_reschedule':
            self.append(event.test_result_id)
            print 'Judge dispatcher: rescheduling:', event
        elif event.type == 'judge_dispatcher_dequeue':
            e = Event(type='judge_dispatcher_dequeue_result')
            e.tag = event.tag
            e.test_result_id = self.pop()
            if not e.test_result_id is None:
                tr = TestResult.objects.get(id=e.test_result_id)
                tr.tester = User.objects.get(id=event.tester_id)
                tr.save()
            print 'JudgeDispatcher: dequeue by', event.tester_id, ':', e
            self.send(e)

class JudgeGenerator(Client2):
    queue = 'judge_generator_queue'

    def start_judge(self, id):
        res = TestSuiteResult.objects.get(id=id)
        print 'Judge generator: starting new judge ', res.test_suite.dispatcher
        (dispatcher_module, dispatcher_func) = res.test_suite.dispatcher.rsplit('.',1)
        accumulators = res.test_suite.accumulators.split(',')
        dispatcher_module = __import__(dispatcher_module, globals(), locals(), [ dispatcher_func ], -1)
        dispatcher = getattr(dispatcher_module, dispatcher_func)
        self.slave.add_client(dispatcher(res, accumulators))

    def _init(self):
        for test_suite_result in TestSuiteResult.objects.filter(pending=True):
        	self.start_judge(test_suite_result.id)
        self.attach(self.queue)
        self.map({'type': 'db', 'model': 'core.testsuiteresult', 'action': 'I'}, self.queue)
        self.map({'type': 'judge_generator_reschedule'}, self.queue)

    def handle_event(self, queue, event):
        if event.type == 'db':
        	self.start_judge(event.object_id)
        elif event.type == 'judge_generator_reschedule':
        	self.start_judge(event.test_suite_result_id)

class default_status_accumulator(object):
    def __init__(self, test_suite_result):
        self.test_suite_result = test_suite_result
        self._status = 'OK'

    def accumulate(self, test_result):
        status = OpenAttribute.get_str(test_result, 'status')
        print 'Default Status Accumulator', self.test_suite_result.id, ':', self._status, '+=', status
        if status is None:
            status = 'INT'
        if self._status == 'OK' and status != 'OK':
        	self._status = status

    def status(self):
        return self._status == 'OK'

    def finish(self):
        print 'Default Status Accumulator', self.test_suite_result.id, ':', self._status, '?'
        OpenAttribute.set_str(self.test_suite_result, 'status', self._status)

class default_serial_dispatcher(Client2):
    def __init__(self, test_suite_result, accumulators):
        super(default_serial_dispatcher, self).__init__()
        self.test_suite_result = test_suite_result
        self.queue = 'dispatcher_' + '_' + str(test_suite_result.id) #TODO: are we sure, that she's the one?
        self.accumulators = []
        for accumulator in accumulators:
            (accumulator_module, accumulator_class) = accumulator.rsplit('.',1)
            accumulator_module = __import__(accumulator_module, globals(), locals(), [ accumulator_class ], -1)
            accumulator = getattr(accumulator_module, accumulator_class)
            self.accumulators.append(accumulator(test_suite_result))

    def _init(self):
        self.attach(self.queue)
        self.map({'type': 'db', 'model': 'core.testresult', 'action': 'U', 'new.pending': True, 'new.submit': self.test_suite_result.submit.id}, self.queue) 

        self.to_check = deque()
        for test in self.test_suite_result.test_suite.tests.all():
        	self.to_check.append(test.id)

        self.send_test()
        
    def send_test(self):
        while self.to_check:
        	next = self.to_check.popleft()
            try:
                result = TestResult.objects.get(submit__id=self.test_suite_result.submit.id, test__id=next)
                if result.pending:
                	return
                print 'Test Result of test', next, 'is known', self.accumulators
                for accumulator in self.accumulators:
                	accumulator.accumulate(result)
                for accumulator in self.accumulators:
                    if not accumulator.status():
                    	break
            #TODO: except concrete exception
            except:
                self.to_check.appendleft(next)
                try:
                    #TODO:transaction
                    transaction.enter_transaction_management()
                    transaction.managed(True)
                    print 'Test Result of test', next, 'is unknown'
                    TestResult(submit=self.test_suite_result.submit, test=Test.objects.get(id=next)).save()
                    transaction.commit()
                    transaction.leave_transaction_management()
                except:
                    transaction.rollback()
                    transaction.leave_transaction_management()
                    pass
                return
        for accumulator in self.accumulators:
        	accumulator.finish()

		self.test_suite_result.pending = False
		self.test_suite_result.save()
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
        self.connection.send(Receive())
        result = self.connection.recv()
        self.lock.release()
        return result[1]
