"""Test suite for satori.core.events.manager.
"""

import unittest

from multiprocessing import Process, Pipe

from satori.ph.objects import Object
from satori.core.events.client import CoroutineClient, ConnectionClient
from satori.core.events.mapper import TrivialMapper
from satori.core.events.manager import Master, Slave
from satori.core.events.protocol import Event, QueueId, KeepAlive, Attach, Detach, Map, Unmap, Send, Receive
from satori.core.events.scheduler import FifoScheduler, PollScheduler


class Tests(Object):

    def testConnect(self):
        def run():
            yield KeepAlive()
        client = CoroutineClient(coroutine=run(), scheduler=self.scheduler)
        self.manager.run()

    def testEcho(self):
        def run():
            queue_id = QueueId("echo")
            yield Attach(queue_id)
            mapping = yield Map(dict(), queue_id)
            message = "Hello, World!"
            event = Event()
            event.message = message
            serial = yield Send(event)
            _, event = yield Receive()
            self.assertEqual(event.serial, serial)
            self.assertEqual(event.message, message)
            yield Unmap(mapping)
            yield Detach(queue_id)
        client = CoroutineClient(coroutine=run(), scheduler=self.scheduler)
        self.manager.run()


class Local(unittest.TestCase, Tests):

    def setUp(self):
        m = TrivialMapper()
        self.scheduler = FifoScheduler()
        self.manager = Master(scheduler=self.scheduler, mapper=m)


class Remote(unittest.TestCase, Tests):

    @staticmethod
    def run_server(connection):
        m = TrivialMapper()
        s = PollScheduler()
        c = ConnectionClient(scheduler=s, connection=connection)
        Master(mapper=m, scheduler=s).run()

    def setUp(self):
        conn1, conn2 = Pipe(True)
        self.server = Process(target=self.run_server, args=(conn1,))
        self.server.start()
        self.scheduler = FifoScheduler()
        self.manager = Slave(scheduler=self.scheduler, connection=conn2)

    def tearDown(self):
        self.server.terminate()
