"""Map events to queues.
"""


from satori.objects import Object, Argument

from .api import Event, MappingId, QueueId


class Mapper(Object):
    """Interface. Maps events to queues.
    """

    @Argument('criteria', type=dict)
    @Argument('queue_id', type=QueueId)
    def map(self, criteria, queue_id):
        """Create a new mapping. Events matching the criteria will be routed to
        the queue with the given (opaque) id. Returns (opaque) mapping id.
        """
        raise NotImplementedError

    @Argument('mapping_id', type=MappingId)
    def unmap(self, mapping_id):
        """Remove an existing mapping given its identifier.
        """
        raise NotImplementedError

    @Argument('event', type=Event)
    def resolve(self, event):
        """Generator. Yield identifiers of queues to which the given event is mapped.
        """
        raise NotImplementedError


class TrivialMapper(Mapper):
    """A trivial Mapper with linear lookup.
    """

    def __init__(self):
        self.mappings = dict()

    def map(self, criteria, queue_id):
        """Create a new mapping. Events matching the criteria will be routed to
        the queue_id with the given (opaque) id. Returns (opaque) mapping_id id.
        """
        mapping_id = None
        while mapping_id is None or mapping_id in self.mappings:
            mapping_id = MappingId()
        self.mappings[mapping_id] = (criteria, queue_id)
        return mapping_id

    def unmap(self, mapping_id):
        """Remove an existing mapping given its identifier.
        """
        del self.mappings[mapping_id]

    def resolve(self, event):
        """Generator. Yield identifiers of queues to which the given event is mapped.
        """
        for criteria, queue_id in self.mappings.itervalues():
            match = True
            for name, value in criteria.iteritems():
                if event.get(name, value) != value:
                    match = False
                    break
            if match:
                yield queue_id
