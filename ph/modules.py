"""Python Hacks that deal with modules."""


import sys
import imp


__all__ = (
	'get_module',
)


def get_module(spec, path=None):
	"""Loads a module by its absolute, qualified name."""
	path = path or sys.path
	module = sys.modules.get(spec, None)
	if module is None:
		module = imp.new_module('(none)')
		module.__path__ = path
		for name in spec.split('.'):
			module = imp.load_module(name, *imp.find_module(name, module.__path__))
	return module
