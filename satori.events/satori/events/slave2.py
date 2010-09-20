from collections import deque
from _multiprocessing import Connection
from satori.objects import Argument
from .protocol import Attach, Detach, Map, Unmap, Send, Receive, KeepAlive, ProtocolError

class Slave2(object):
    @Argument('connection', type=Connection)
    def __init__(self, connection):
        self.connection = connection
        self.queue_clients = dict()
        self.clients = set()
        self.added_clients = set()
        self.removed_clients = set()

    def attach(self, client, queue):
        if queue not in self.queue_clients:
            self.connection.send(Attach(queue))
            self.connection.recv()
            self.queue_clients[queue] = deque()
        self.queue_clients[queue].append(client)

    def detach(self, client, queue):
        if queue in self.queue_clients:
            self.queue_clients[queue].remove(client)
            if not self.queue_clients[queue]:
                self.connection.send(Detach(queue))
                self.connection.recv()
                del self.queue_clients[queue]

    def map(self, criteria, queue):
        self.connection.send(Map(criteria, queue))
        return self.connection.recv()

    def unmap(self, mapping):
        self.connection.send(Unmap(mapping))
        self.connection.recv()
        
    def send(self, event):
        self.connection.send(Send(event))
        self.connection.recv()

    def add_client(self, client):
        self.added_clients.add(client)

    def remove_client(self, client):
        self.removed_clients.add(client)

    def run(self):
        try:
            while True:
                if self.added_clients:
                    for client in self.added_clients:
                        self.clients.add(client)
                        client.init(self)

                    self.added_clients.clear()

                if self.removed_clients:
                    for client in self.removed_clients:
                        for queue in set(self.queue_clients):
                            if client in self.queue_clients[queue]:
                                self.detach(client, queue)

                        client.deinit()
                        self.clients.remove(client)

                    self.removed_clients.clear()

                self.connection.send(Receive())
                (queue, event) = self.connection.recv()
                if queue in self.queue_clients:
                    client = self.queue_clients[queue].popleft()
                    client.handle_event(queue, event)
                    self.queue_clients[queue].append(client)
        finally:
            for client in self.clients:
                for queue in set(self.queue_clients):
                    if client in self.queue_clients[queue]:
                        self.detach(client, queue)

                client.deinit()

            self.clients.clear()

        self.connection.send(Disconnect())
        self.connection.recv()

        self.running = False

