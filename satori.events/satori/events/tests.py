# vim:ts=4:sts=4:sw=4:expandtab
"""Test suite for satori.events.manager.
"""

import unittest

from multiprocessing import Process, Pipe

from .api import Event, QueueId
from .protocol import KeepAlive, Attach, Detach, Map, Unmap, Send, Receive
from .mapper import TrivialMapper
from .master import Master
from .slave import Slave


class TestCommunication(unittest.TestCase):
    """Test simple communication scenarios.
    """

    @staticmethod
    def _server(connection):
        master = Master(mapper=TrivialMapper())
        master.connectSlave(connection)
        master.run()

    def setUp(self):
        """Prepare test environment.
        """
        conn1, conn2 = Pipe(True)
        self.server = Process(target=self._server, args=(conn1,))
        self.server.start()
        self.manager = Slave(connection=conn2)

    def testConnect(self):
        """Test scenario: connect and disconnect.
        """
        def _procedure():
            yield KeepAlive()
        self.manager.schedule(_procedure())
        self.manager.run()

    def testEcho(self):
        """Test scenario: send and receive the same event.
        """
        def _procedure():
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
        self.manager.schedule(_procedure())
        self.manager.run()

    def tearDown(self):
        """Clean up.
        """
        self.server.terminate()
