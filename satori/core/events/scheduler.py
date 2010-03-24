import collections
import select

from satori.ph.objects import Object, Argument


class Scheduler(Object):
    """Interface. Chooses which Client to run next.
    """

    def next(self):
        raise NotImplementedError()


class FifoScheduler(Scheduler):
    """A simple FIFO Scheduler.
    """

    def __init__(self):
        self.fifo = collections.deque()

    def next(self):
        if len(self.fifo) > 0:
            return self.fifo.popleft()
        return None

    def add(self, client):
        self.fifo.append(client)


class PollScheduler(Scheduler):
    """A Scheduler using select.poll on file descriptors.
    """

    def __init__(self):
        self.waits = select.poll()
        self.fdmap = dict()
        self.ready = collections.deque()

    def next(self):
        while len(self.ready) == 0:
            for fd, ev in self.waits.poll():
                client = self.fdmap[fd]
                if ev & (select.POLLERR | select.POLLHUP) != 0:
                    self.remove(client)
                self.ready.append(client)
        return self.ready.popleft()

    def add(self, client):
        fd = client.fd
        if fd in self.fdmap:
            return
        self.fdmap[fd] = client
        self.waits.register(fd, select.POLLIN | select.POLLHUP | select.POLLERR)

    def remove(self, client):
        fd = client.fd
        if fd not in self.fdmap:
            return
        del self.fdmap[fd]
        self.waits.unregister(fd)
