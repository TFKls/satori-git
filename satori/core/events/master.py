"""Master (central) event coordinator.
"""


import collections
import select
from _multiprocessing import Connection
from multiprocessing.connection import Listener

from satori.ph.objects import Argument

from .api import Manager
from .client import Client, Scheduler
from .mapper import Mapper
from .protocol import Command, KeepAlive, ProtocolError


class PollScheduler(Scheduler):
    """A Scheduler using select.poll on file descriptors.
    """

    def __init__(self):
        self.waits = select.poll()
        self.fdmap = dict()
        self.ready = collections.deque()

    def next(self):
        """Return the next Client to handle.

        A Client is available when its file descriptor is ready to be read from.
        Available Clients are scheduler in a round-robin fashion.
        """
        while len(self.ready) == 0:
            for fileno, event in self.waits.poll():
                client = self.fdmap[fileno]
                if event & (select.POLLERR | select.POLLHUP) != 0:
                    self.remove(client)
                self.ready.append(client)
        return self.ready.popleft()

    def add(self, client):
        """Add a Client to this Scheduler.
        """
        fileno = client.fileno
        if fileno in self.fdmap:
            return
        self.fdmap[fileno] = client
        self.waits.register(fileno, select.POLLIN | select.POLLHUP | select.POLLERR)

    def remove(self, client):
        """Remove a Client from this Scheduler.
        """
        fileno = client.fileno
        if fileno not in self.fdmap:
            return
        self.waits.unregister(fileno)
        del self.fdmap[fileno]


class ConnectionClient(Client):
    """Out-of-process Client communicating over multiprocessing.Connection.
    """

    @Argument('scheduler', type=PollScheduler)
    @Argument('connection', type=Connection)
    def __init__(self, connection):
        self.connection = connection
        self.scheduler.add(self)

    def sendResponse(self, response):
        """Send a response to this Client.
        """
        self.connection.send(response)

    def recvCommand(self):
        """Receive the next command from this Client.
        """
        command = self.connection.recv()
        if not isinstance(command, Command):
            raise ProtocolError("received object is not a Command")
        return command

    def disconnect(self):
        """Disconnect this Client.
        """
        self.scheduler.remove(self)
        self.connection.close()

    fileno = property(lambda self: self.connection.fileno())


class ListenerClient(Client):
    """In-process Client wrapping a multiprocessing.connection.Listener.
    """

    @Argument('scheduler', type=PollScheduler)
    @Argument('listener', type=Listener)
    def __init__(self, listener):
        self.listener = listener

    def sendResponse(self, response):
        """Send a response to this Client.
        """
        pass

    def recvCommand(self):
        """Receive the next command from this Client.
        """
        try:
            connection = self.listener.accept()
        except:
            raise ProtocolError("Listener.accept() failed")
        ConnectionClient(scheduler=self.scheduler, connection=connection)
        return KeepAlive()

    def disconnect(self):
        """Disconnect this Client.
        """
        self.scheduler.remove(self)
        self.listener.close()

    # pylint: disable-msg=W0212
    fileno = property(lambda self: self.listener._listener._socket.fileno())
    # pylint: enable-msg=W0212



class Master(Manager):
    """The central Event Manager.
    """

    @Argument('mapper', type=Mapper)
    def __init__(self, mapper):
        self.mapper = mapper
        self.scheduler = PollScheduler()
        self.serial = 0

    def connectSlave(self, connection):
        """Attach a new Slave over the given connection.
        """
        ConnectionClient(scheduler=self.scheduler, connection=connection)

    def listen(self, listener):
        """Listen for new Slave connections using the given Listener.
        """
        ListenerClient(scheduler=self.scheduler, listener=listener)

    def _handleKeepAlive(self, _command, sender):
        sender.sendResponse(None)

    def _handleDisconnect(self, _command, sender):
        sender.disconnect()

    def _handleAttach(self, command, sender):
        self.dispatcher.attach(sender, command.queue_id)
        sender.sendResponse(None)

    def _handleDetach(self, command, sender):
        self.dispatcher.detach(sender, command.queue_id)
        sender.sendResponse(None)

    def _handleMap(self, command, sender):
        mapping_id = self.mapper.map(command.criteria, command.queue_id)
        sender.sendResponse(mapping_id)

    def _handleUnmap(self, command, sender):
        self.mapper.unmap(command.mapping_id)
        sender.sendResponse(None)

    def _handleSend(self, command, sender):
        event = command.event
        event.serial = self.serial
        self.serial += 1
        sender.sendResponse(event.serial)
        for queue_id in self.mapper.resolve(event):
            self.dispatcher.enqueue(queue_id, event)

    def _handleReceive(self, _command, sender):
        self.dispatcher.activate(sender)
