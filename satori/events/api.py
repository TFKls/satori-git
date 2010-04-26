# vim:ts=4:sts=4:sw=4:expandtab
"""The public API of satori.events.
"""


import hashlib
import random

from satori.objects import Object
from satori.events.misc import Namespace

from .dispatcher import Dispatcher
from .protocol import KeepAlive, Disconnect, Attach, Detach, Map, Unmap, Send, Receive


__all__ = (
    'Event',
    'MappingId', 'QueueId',
    'Manager',
)


class Event(Namespace):
    """Describes an event.
    """

    pass


class MappingId(str):                                          # pylint: disable-msg=R0904
    """A (globally-unique) identifier of a mapping.
    """

    def __new__(cls, value=None):
        if value is None:
            value = hashlib.md5(str(random.getrandbits(512))).hexdigest()
        return str.__new__(cls, value)


class QueueId(str):                                            # pylint: disable-msg=R0904
    """A (globally-unique) identifier of an event queue.
    """
    pass


class Manager(Object):
    """Abstract. Manages Clients within a single process.
    """

    def __init__(self):
        self.dispatcher = Dispatcher()

    def run(self):
        """Execute this Manager's event loop.
        """
        handlers = {
            KeepAlive:  self._handleKeepAlive,
            Attach:     self._handleAttach,
            Detach:     self._handleDetach,
            Map:        self._handleMap,
            Unmap:      self._handleUnmap,
            Send:       self._handleSend,
            Receive:    self._handleReceive,
            Disconnect: self._handleDisconnect,
        }
        while True:
            client = self.scheduler.next()
            if client is None:
                break
            try:
                command = client.recvCommand()
            except StopIteration:
                command = Disconnect()
            handlers[command.__class__](command, client)

    def _handleKeepAlive(self, command, sender):
        raise NotImplementedError()

    def _handleDisconnect(self, command, sender):
        raise NotImplementedError()

    def _handleAttach(self, command, sender):
        raise NotImplementedError()

    def _handleDetach(self, command, sender):
        raise NotImplementedError()

    def _handleMap(self, command, sender):
        raise NotImplementedError()

    def _handleUnmap(self, command, sender):
        raise NotImplementedError()

    def _handleSend(self, command, sender):
        raise NotImplementedError()

    def _handleReceive(self, command, sender):
        raise NotImplementedError()

