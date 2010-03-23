import hashlib
import random

from satori.ph.objects import Object, Argument
from satori.ph.misc import Namespace


__all__ = (
	'Event',
	'MappingId', 'QueueId',
	'Attach', 'Detach',
	'Map', 'Unmap',
	'Send', 'Receive',
	'KeepAlive', 'Disconnect',
	'ProtocolError',
)


class Event(Namespace):
	pass


class MappingId(str):

	def __new__(cls, value=None):
		if value is None:
			value = hashlib.md5(str(random.getrandbits(512))).hexdigest()
		return str.__new__(cls, value)


class QueueId(str):
	pass


class Command(object):
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
