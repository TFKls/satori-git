# vim:ts=4:sts=4:sw=4:expandtab
"""Package. Manages event queues.

Writing event-driven code
-------------------------

Event-driven procedures should be written as python coroutines (extended generators).
To call the event API, yield an instance of the appropriate command. You can use
sub-procedures - just yield the appropriate generator (a minor nuisance is that you
cannot have such sub-procedure return a value).

Example
-------

.. code:: python

    from satori.events import *

    def countdown():
        queue = QueueId('any string will do')
        mapping = yield Map({}, queue)
        yield Attach(queue)
        yield Send(Event(left=10))
        while True:
            q, event = yield Receive()
            if event.left == 0:
                break
            event.left -= 1
            yield Send(event)
        yield Unmap(mapping)
        yield Detach(queue)

"""


from .api import Event, MappingId, QueueId
from .protocol import Attach, Detach
from .protocol import Map, Unmap
from .protocol import Send, Receive
from .protocol import KeepAlive, Disconnect, ProtocolError
from .api import Manager
from .master import Master
from .slave import Slave
from .client2 import Client2
from .slave2 import Slave2


__all__ = (
    'Event', 'MappingId', 'QueueId',
    'Attach', 'Detach',
    'Map', 'Unmap',
    'Send', 'Receive',
    'KeepAlive', 'ProtocolError',
    'Master', 'Slave',
)
