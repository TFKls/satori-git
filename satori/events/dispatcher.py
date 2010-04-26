# vim:ts=4:sts=4:sw=4:expandtab
"""Matching Clients with event queues.
"""


import collections

from satori.objects import Object
from satori.misc import Namespace


class Dispatcher(Object):
    """Abstract. Dispatches Events to Clients.
    """

    def __init__(self):
        self.queues = dict()
        self.clients = dict()

    def _qdata(self, queue_id):
        if queue_id not in self.queues:
            qdata = Namespace()
            qdata.references = 0
            qdata.events = collections.deque()
            qdata.clients = collections.deque()
            self.queues[queue_id] = qdata
        return self.queues[queue_id]

    def _cdata(self, client):
        if client not in self.clients:
            cdata = Namespace()
            cdata.queue_ids = set()
            cdata.active = False
            self.clients[client] = cdata
        return self.clients[client]

    def attach(self, client, queue_id):
        """Declare Client's interest in events from a given queue.
        """
        qdata = self._qdata(queue_id)
        cdata = self._cdata(client)
        if queue_id not in cdata.queue_ids:
            cdata.queue_ids.add(queue_id)
            qdata.references += 1

    def detach(self, client, queue_id):
        """Revoke Client's interest in events from a given queue.
        """
        qdata = self._qdata(queue_id)
        cdata = self._cdata(client)
        if queue_id in cdata.queues:
            cdata.queue_ids.remove(queue_id)
            qdata.references -= 1
        if qdata.references == 0:
            yield queue_id
            del self.queues[queue_id]

    def activate(self, client):
        """Mark a Client as ready to receive a (single) event.
        """
        cdata = self._cdata(client)
        best = None
        for queue_id in cdata.queue_ids:
            qdata = self._qdata(queue_id)
            if len(qdata.events) > 0:
                event = qdata.events[0]
                if best is None or best[1] > event.serial:
                    best = (queue_id, event.serial)
        if best is not None:
            qdata = self._qdata(best[0])
            client.sendResponse((best[0], qdata.events.popleft()))
            return
        for queue_id in cdata.queue_ids:
            qdata = self._qdata(queue_id)
            qdata.clients.append(client)
        cdata.active = True

    def enqueue(self, queue_id, event):
        """Add a new event to a given queue.
        """
        qdata = self._qdata(queue_id)
        qdata.events.append(event)
        while len(qdata.clients) > 0:
            client = qdata.clients.popleft()
            cdata = self._cdata(client)
            if not cdata.active:
                continue
            if queue_id not in cdata.queue_ids:
                continue
            cdata.active = False
            client.sendResponse((queue_id, qdata.events.popleft()))
            return
