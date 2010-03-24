from _multiprocessing import Connection
from multiprocessing.connection import Listener
from types import GeneratorType

from satori.ph.objects import Object, Argument
from satori.ph.misc import flatten_coroutine
from satori.core.events.protocol import Command, KeepAlive, ProtocolError
from satori.core.events.scheduler import Scheduler, FifoScheduler, PollScheduler


class Client(Object):
    """Abstract. Base for client implementations.
    """

    @Argument('scheduler', type=Scheduler)
    def __init__(self, scheduler):
        self.scheduler = scheduler

    def sendResponse(self, response):
        raise NotImplementedError()

    def recvCommand(self):
        raise NotImplementedError()

    def disconnect(self):
        raise NotImplementedError()


class CoroutineClient(Client):
    """In-process Client implemented as a coroutine.
    """

    @Argument('scheduler', type=FifoScheduler)
    @Argument('coroutine', type=GeneratorType)
    def __init__(self, coroutine):
        self.coroutine = flatten_coroutine(coroutine)
        self.response  = None
        self.scheduler.add(self)

    def sendResponse(self, response):
        if self.response is not None:
            raise ProtocolError("sendResponse() called twice without an intervening recvCommand()")
        self.response = response
        self.scheduler.add(self)

    def recvCommand(self):
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
        self.connection.send(response)

    def recvCommand(self):
        command = self.connection.recv()
        if not isinstance(command, Command):
            raise ProtocolError("received object is not a Command")
        return command

    def disconnect(self):
        self.scheduler.remove(self)
        self.connection.close()

    fd = property(lambda self: self.connection.fileno())


class ListenerClient(Client):
    """In-process Client wrapping a multiprocessing.connection.Listener.
    """

    @Argument('scheduler', type=PollScheduler)
    @Argument('listener', type=Listener)
    def __init__(self, listener):
        self.listener = listener

    def sendResponse(self, response):
        pass

    def recvCommand(self):
        try:
            connection = self.listener.accept()
        except:
            raise ProtocolError("Listener.accept() failed")
        client = ConnectionClient(scheduler=self.scheduler, connection=connection)
        return KeepAlive()

    def disconnect(self):
        self.scheduler.remove(self)
        self.listener.close()

    fd = property(lambda self: self.listener._listener._socket.fileno())
