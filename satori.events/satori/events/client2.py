class Client2(object):
    def __init__(self):
        super(Client2, self).__init__()

    def _init(self):
        pass

    def init(self, slave):
        self.slave = slave
        self._init()

    def _deinit(self):
        pass

    def deinit(self):
        self._deinit()

    def finish(self):
        self.slave.remove_client(self)

    def handle_event(self, queue, event):
        pass

    def attach(self, queue):
        return self.slave.attach(self, queue)
    
    def detach(self, queue):
        return self.slave.detach(self, queue)

    def map(self, criteria, queue):
        return self.slave.map(criteria, queue)

    def unmap(self, mapping):
        return self.slave.unmap(mapping)

    def send(self, event):
        return self.slave.send(event)
