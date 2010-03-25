"""Client scheduling policies.
"""


import collections
import select

from satori.ph.objects import Object


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


class FifoScheduler(Scheduler):
    """A simple FIFO Scheduler.
    """

    def __init__(self):
        self.fifo = collections.deque()

    def next(self):
        """Return the next Client to handle.
        
        The Clients are returned in the order in which they are added.
        """
        if len(self.fifo) > 0:
            return self.fifo.popleft()
        return None

    def add(self, client):
        """Add a Client to this Scheduler.
        """
        self.fifo.append(client)

    def remove(self, client):
        """Does nothing. Clients are removed when they are scheduled.
        """
        pass


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
