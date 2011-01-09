# vim:ts=4:sts=4:sw=4:expandtab
import os
import logging
from django.conf import settings
from threading import local, current_thread
from multiprocessing import current_process
from multiprocessing.connection import Client
from satori.events import Event, Attach, Map, Send, Receive

class CheckQueueClient(local):
    def new_connection(self):
        self.pid = current_process().pid
        self.tid = current_thread().ident
        logging.info('Starting check queue client connection for pid %s tid %s', self.pid, self.tid)
        self.tag = str(self.pid) + '_' + str(self.tid)
        self.queue = 'check_queue_client_' + self.tag
        self.connection = Client(address=(settings.EVENT_HOST, settings.EVENT_PORT))
        self.connection.send(Attach(self.queue))
        self.connection.recv()
        self.connection.send(Map({'type': 'checking_test_result_dequeue_result', 'tag': str(self.tag)}, self.queue))
        self.connection.recv()

    def __init__(self):
        self.new_connection()

    def get_next(self, role):
        if (self.pid != current_process().pid) or (self.tid != current_thread().ident):
            self.new_connection()
        self.connection.send(Send(Event(type='checking_test_result_dequeue', tag=str(self.tag), tester_id=role.id)))
        self.connection.recv()
        self.connection.send(Receive())
        result = self.connection.recv()
        logging.debug('Check queue client: received %s for pid %s tid %s', result[1], self.pid, self.tid)
        return result[1]

check_queue_client = CheckQueueClient()
