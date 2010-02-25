"""Useful additions to the standard Pyhton class hierarchy."""


__all__ = (
	'Object',
)


from ph.exceptions import ArgumentError


class Object(object):
	"""A better replacement for 'object'.
	Supports super() constructor chaining.
	"""

	def __init__(self, *args, **kwargs):
		self.__kwargs = kwargs
	
	KWARGREQ = "{0} constructor requires a keyword argument '{1}' of type '{2}'"
	
	def required_argument(self, name, type_):
		try:
			value = self.__kwargs[name]
			if type_ is not None and not isinstance(value, type_):
				raise KeyError
			setattr(self, name, value)
		except KeyError:
			raise ArgumentError(Object.KWARGREQ.format(self.__class__.__name__, name, type_.__name__))

	def optional_argument(self, name, type_, default):
		try:
			value = self.__kwargs.get(name, default)
			if type_ is not None and not isinstance(value, type_):
				raise KeyError
			setattr(self, name, value)
		except KeyError:
			raise ArgumentError(Object.KWARGREQ.format(self.__class__.__name__, name, type_.__name__))
