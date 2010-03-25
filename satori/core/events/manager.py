"""Event Manager implementations.
"""


__all__ = ('Master', 'Slave')


from _multiprocessing import Connection

from satori.ph.objects import Object, Argument
from satori.core.events.dispatcher import Dispatcher
from satori.core.events.mapper import Mapper
from satori.core.events.protocol import KeepAlive, Disconnect, Attach, Detach
from satori.core.events.protocol import Map, Unmap, Send, Receive
from satori.core.events.scheduler import Scheduler


class Manager(Object):
    """Manages Clients within a single process.
    """

    @Argument('scheduler', type=Scheduler)
    def __init__(self, scheduler):
        self.scheduler = scheduler
        self.dispatcher = Dispatcher()

    def doKeepAlive(self, _command, sender):
        """Handle KeepAlive command.
        """
        sender.sendResponse(None)

    def doDisconnect(self, _command, sender):
        """Handle Disconnect command.
        """
        sender.disconnect()

    def run(self):
        """Execute this Manager's event loop.
        """
        processors = {
            KeepAlive:  self.doKeepAlive,
            Attach:     self.doAttach,
            Detach:     self.doDetach,
            Map:        self.doMap,
            Unmap:      self.doUnmap,
            Send:       self.doSend,
            Receive:    self.doReceive,
            Disconnect: self.doDisconnect,
        }
        while True:
            client = self.scheduler.next()
            if client is None:
                break
            try:
                command = client.recvCommand()
            except StopIteration:
                command = Disconnect()
            processors[command.__class__](command, client)


class Master(Manager):
    """The central Event Manager.
    """

    @Argument('mapper', type=Mapper)
    def __init__(self, mapper):
        self.mapper = mapper
        self.serial = 0

    def doAttach(self, command, sender):
        """Handle Attach command.
        """
        self.dispatcher.attach(sender, command.queue_id)
        sender.sendResponse(None)

    def doDetach(self, command, sender):
        """Handle Detach command.
        """
        self.dispatcher.detach(sender, command.queue_id)
        sender.sendResponse(None)

    def doMap(self, command, sender):
        """Handle Map command.
        """
        mapping_id = self.mapper.map(command.criteria, command.queue_id)
        sender.sendResponse(mapping_id)

    def doUnmap(self, command, sender):
        """Handle Unmap command.
        """
        self.mapper.unmap(command.mapping_id)
        sender.sendResponse(None)

    def doSend(self, command, sender):
        """Handle Send command.
        """
        event = command.event
        event.serial = self.serial
        self.serial += 1
        sender.sendResponse(event.serial)
        for queue_id in self.mapper.resolve(event):
            self.dispatcher.enqueue(queue_id, event)

    def doReceive(self, _command, sender):
        """Handle Receive command.
        """
        self.dispatcher.activate(sender)


class Slave(Manager):
    """A Manager which acts a remote Client.
    """

    @Argument('connection', type=Connection)
    def __init__(self, connection):
        self.connection = connection
        self.queue_refs = dict()

    def doAttach(self, command, sender):
        """Handle Attach command.
        """
        if command.queue_id in self.queue_refs:
            self.queue_refs[command.queue_id] += 1
        else:
            self.connection.send(command)
            self.connection.recv()
            self.queue_refs[command.queue_id] = 1
        self.dispatcher.attach(sender, command.queue_id)
        sender.sendResponse(None)

    def doDetach(self, command, sender):
        """Handle Detach command.
        """
        if command.queue_id in self.queue_refs:
            self.queue_refs[command.queue_id] -= 1
            if self.queue_refs[command.queue_id] == 0:
                self.connection.send(command)
                self.connection.recv()
                del self.queue_refs[command.queue_id]
        self.dispatcher.detach(sender, command.queue_id)
        sender.sendResponse(None)

    def doMap(self, command, sender):
        """Handle Map/Unmap/Send commands.
        """
        self.connection.send(command)
        response = self.connection.recv()
        sender.sendResponse(response)

    doUnmap = doMap

    doSend = doMap

    def doReceive(self, command, sender):
        """Handle Receive command.
        """
        self.dispatcher.activate(sender)
        self.connection.send(command)
        response = self.connection.recv()
        if isinstance(response, Exception):
            pass # TODO: handle exceptions
        self.dispatcher.enqueue(response[0], response[1])
