"""Wrappers for event producers/consumers.
"""


from _multiprocessing import Connection
from multiprocessing.connection import Listener
from types import GeneratorType

from satori.ph.objects import Object, Argument
from satori.ph.misc import flattenCoroutine
from satori.core.events.protocol import Command, KeepAlive, ProtocolError
from satori.core.events.scheduler import Scheduler, FifoScheduler, PollScheduler


class Client(Object):
    """Abstract. Base for client implementations.
    """

    @Argument('scheduler', type=Scheduler)
    def __init__(self, scheduler):
        self.scheduler = scheduler

    def sendResponse(self, response):
        """Send a response to this Client.
        """
        raise NotImplementedError()

    def recvCommand(self):
        """Receive the next command from this Client.
        """
        raise NotImplementedError()

    def disconnect(self):
        """Disconnect this Client.
        """
        raise NotImplementedError()


class CoroutineClient(Client):
    """In-process Client implemented as a coroutine.
    """

    @Argument('scheduler', type=FifoScheduler)
    @Argument('coroutine', type=GeneratorType)
    def __init__(self, coroutine):
        self.coroutine = flattenCoroutine(coroutine)
        self.response  = None
        self.scheduler.add(self)

    def sendResponse(self, response):
        """Send a response to this Client.

        The response is saved and delivered to the coroutine on the next call to
        recvCommand().
        """
        if self.response is not None:
            raise ProtocolError(
                "sendResponse() called twice without an intervening recvCommand()")
        self.response = response
        self.scheduler.add(self)

    def recvCommand(self):
        """Receive the next command from this Client.
        """
        response = self.response
        self.response = None
        if isinstance(response, Exception):
            command = self.coroutine.throw(response)
        else:
            command = self.coroutine.send(response)
        if not isinstance(command, Command):
            raise ProtocolError("received object is not a Command")
        return command

    def disconnect(self):
        """Disconnect this Client.
        """
        self.response = ProtocolError()


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
