# vim:ts=4:sts=4:sw=4:expandtab
"""The protocol for event-driven code.
"""


from satori.objects import Object


__all__ = (
    'KeepAlive', 'Disconnect',
    'Attach', 'Detach',
    'Map', 'Unmap',
    'Send', 'Receive',
    'ProtocolError',
)


class Command(Object):
    """Abstract. Base for event command classes.
    """

    __slots__ = ()


class KeepAlive(Command):
    """Command: do nothing.
    """

    __slots__ = ()


class Attach(Command):
    """Command: attach to an event queue_id.
    """

    __slots__ = ('queue_id')

    def __init__(self, queue_id):
        self.queue_id = queue_id


class Detach(Command):
    """Command: detach from an event queue_id.
    """

    __slots__ = ('queue_id')

    def __init__(self, queue_id):
        self.queue_id = queue_id


class Map(Command):
    """Command: add event mapping_id.
    """

    __slots__ = ('criteria', 'queue_id')

    def __init__(self, criteria, queue_id):
        self.criteria = criteria
        self.queue_id = queue_id


class Unmap(Command):
    """Command: remove event mapping_id.
    """

    __slots__ = ('mapping_id')

    def __init__(self, mapping_id):
        self.mapping_id = mapping_id


class Send(Command):
    """Command: send an event.
    """

    __slots__ = ('event')

    def __init__(self, event):
        self.event = event


class Receive(Command):
    """Command: receive a single event.
    """

    __slots__ = ()


class Disconnect(Command):
    """Command: disconnect from the server.
    """

    __slots__ = ()


class ProtocolError(Exception):
    """Signifies an error in the communication protocol.
    """

    pass
