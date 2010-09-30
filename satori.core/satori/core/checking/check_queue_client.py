# vim:ts=4:sts=4:sw=4:expandtab
import os
from django.conf import settings
from threading import Lock
from multiprocessing.connection import Client
from satori.events import Event, Attach, Map, Send, Receive

class CheckQueueClient(object):
    _pid = -1

    @classmethod
    def get_instance(cls):
        pid = os.getpid()
        if pid != cls._pid:
            cls._instance = CheckQueueClient(pid=pid)
            cls._pid = pid
        return cls._instance

    def __init__(self, pid):
        self.lock = Lock()
        self.lock.acquire()
        self.connection = Client(address=(settings.EVENT_HOST, settings.EVENT_PORT))
        queue = 'check_queue_client_' + str(pid)
        self.connection.send(Attach(queue))
        self.connection.recv()
        self.connection.send(Map({'type': 'check_queue_dequeue_result', 'tag': str(pid)}, queue))
        self.connection.recv()
        self.lock.release()

    def get_next(self, user):
        self.lock.acquire()
        self.connection.send(Send(Event(type='check_queue_dequeue', tag=str(self._pid), tester_id=user.id)))
        self.connection.recv()
        self.connection.send(Receive())
        result = self.connection.recv()
        self.lock.release()
        return result[1]
