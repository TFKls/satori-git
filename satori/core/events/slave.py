"""A slave (satellite) event coordinator.
"""


import collections
from _multiprocessing import Connection

from satori.objects import Argument

from .api import Manager
from .client import CoroutineClient, Scheduler


class FifoScheduler(Scheduler):
    """A simple FIFO Scheduler.
    """

    def __init__(self):
        self.fifo = collections.deque()

    def next(self):
        """Return the next Client to handle.

        The Clients are returned in the order in which they are added.
        """
        if len(self.fifo) > 0:
            return self.fifo.popleft()
        return None

    def add(self, client):
        """Add a Client to this Scheduler.
        """
        self.fifo.append(client)

    def remove(self, client):
        """Does nothing. Clients are removed when they are scheduled.
        """
        pass


class Slave(Manager):
    """A Manager which acts a remote Client.
    """

    @Argument('connection', type=Connection)
    def __init__(self, connection):
        self.connection = connection
        self.scheduler = FifoScheduler()
        self.queue_refs = dict()

    def schedule(self, coroutine):
        """Schedule the given coroutine to run within this Slave.
        """
        CoroutineClient(scheduler=self.scheduler, coroutine=coroutine)

    def _handleKeepAlive(self, _command, sender):
        sender.sendResponse(None)

    def _handleDisconnect(self, _command, sender):
        sender.disconnect()

    def _handleAttach(self, command, sender):
        if command.queue_id in self.queue_refs:
            self.queue_refs[command.queue_id] += 1
        else:
            self.connection.send(command)
            self.connection.recv()
            self.queue_refs[command.queue_id] = 1
        self.dispatcher.attach(sender, command.queue_id)
        sender.sendResponse(None)

    def _handleDetach(self, command, sender):
        if command.queue_id in self.queue_refs:
            self.queue_refs[command.queue_id] -= 1
            if self.queue_refs[command.queue_id] == 0:
                self.connection.send(command)
                self.connection.recv()
                del self.queue_refs[command.queue_id]
        self.dispatcher.detach(sender, command.queue_id)
        sender.sendResponse(None)

    def _forward(self, command, sender):
        self.connection.send(command)
        response = self.connection.recv()
        sender.sendResponse(response)

    def _handleMap(self, command, sender):
        return self._forward(command, sender)

    def _handleUnmap(self, command, sender):
        return self._forward(command, sender)

    def _handleSend(self, command, sender):
        return self._forward(command, sender)

    def _handleReceive(self, command, sender):
        self.dispatcher.activate(sender)
        self.connection.send(command)
        response = self.connection.recv()
        if isinstance(response, Exception):
            pass # TODO: handle exceptions
        self.dispatcher.enqueue(response[0], response[1])
