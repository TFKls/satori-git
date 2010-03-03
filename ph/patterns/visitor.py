"""Decorators implementing the Visitor pattern (performing dynamic method dispatch
based on the type of argument other than self."""


__all__ = (
	'Dispatch', 'Implement',
)


from sys import _getframe
from types import TypeType

from ph.objects import Object, Argument


class Dispatch(Object):
	"""Decorator. Marks the base implementation of a dynamically dispatched function."""

	@Argument('argument', "the index or name of the argument to dispatch on", type=(int,str))
	def __init__(self, args):
		self.argument = args.argument

	def __call__(self, function):
		def _dispatch(*args, **kwargs):
			arg = _dispatch.func_dict['argument']					# pylint: disable-msg=E1101
			imp = _dispatch.func_dict['implementations']			# pylint: disable-msg=E1101
			default = _dispatch.func_dict['default']				# pylint: disable-msg=E1101
			if isinstance(arg, int):
				key = args[arg]
			else:
				key = kwargs[arg]
			for class_ in key.__class__.__mro__:
				if class_ in imp:
					return imp[class_](*args, **kwargs)
			return default(*args, **kwargs)
		_dispatch.__name__ = function.__name__  					# pylint: disable-msg=W0622
		_dispatch.__doc__ = function.__doc__ 						# pylint: disable-msg=W0622
		_dispatch.func_dict['argument'] = self.argument 			# pylint: disable-msg=E1101
		_dispatch.func_dict['implementations'] = dict()				# pylint: disable-msg=E1101
		_dispatch.func_dict['default'] = function					# pylint: disable-msg=E1101
		return _dispatch


class Implement(Object):
	"""
	Decorator. Marks a specialized implementation of the dynamically dispatched function.
	"""

	@Argument('type', "the argument type handled by this implementation", type=TypeType)
	def __init__(self, args):
		self.type = args.type

	def __call__(self, function):
		dispatch = _getframe(1).f_locals[function.__name__]
		dispatch.func_dict['implementations'][self.type] = function	# pylint: disable-msg=E1101
		return dispatch

