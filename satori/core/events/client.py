"""Communications and scheduling of event clients.
"""


from types import GeneratorType

from satori.ph.objects import Object, Argument
from satori.ph.misc import flattenCoroutine
from satori.core.events.protocol import Command, ProtocolError


class Scheduler(Object):
    """Interface. Chooses which Client to run next.
    """

    def next(self):
        """Return the next Client to handle.
        """
        raise NotImplementedError()

    def add(self, client):
        """Add a Client to this Scheduler.
        """
        raise NotImplementedError()

    def remove(self, client):
        """Remove a Client from this Scheduler.
        """
        raise NotImplementedError()


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
