"""Miscellanea."""

__all__ = (
	'Namespace',
)


class Namespace(dict):
	"""A dictionary whose elements can be accessed as attibutes.
	"""

	def __init__(self, *args, **kwargs):
		dict.__init__(self, *args, **kwargs)
	
	def __hasattr__(self, key):
		return key in self

	def __getattr__(self, key):
		return self[key]
	
	def __setattr__(self, key, value):
		self[key] = value
	
	def __delattr__(self, key):
		del self[key]
