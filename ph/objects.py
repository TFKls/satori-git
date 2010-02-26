"""Useful additions to the standard Pyhton class hierarchy."""


__all__ = (
	'Object', 'Argument',
)


from ph.exceptions import ArgumentError
from ph.misc import Namespace


class TypeSpec(object):
	"""An argument type specification."""

	def __init__(self, **kwargs):
		self.type = kwargs.get('type', [])
		self.none = kwargs.get('none', len(self.type) == 0)
	
	def __and__(self, other):
		type_ = self.type + other.type
		none = self.none and other.none
		return TypeSpec(type=type_, none=none)
	
	def __str__(self):
		return str(self.type + (self.none and [] or ['not None']))
	
	def isValid(self, value):
		"""Checks whether a given value meets this TypeSpec."""
		if value is None:
			return self.none
		for type_ in self.type:
			if not isinstance(value, type_):
				return False
		return True


class ValueSpec(object):
	"""An argument value specification."""

	REQUIRED = 0
	OPTIONAL = 1
	PROVIDED = 2

	def __init__(self, **kwargs):
		self.value = None
		self.mode = ValueSpec.REQUIRED
		if 'default' in kwargs:
			self.value = kwargs['default']
			self.mode = ValueSpec.OPTIONAL
		if 'fixed' in kwargs:
			self.value = kwargs['fixed']
			self.mode = ValueSpec.PROVIDED
	
	def __add__(self, other):
		# one witout a value always looses...
		if (self.mode == ValueSpec.REQUIRED):
			return other
		if (other.mode == ValueSpec.REQUIRED):
			return self
		# ...two strongmen agree or die...
		if (self.mode == ValueSpec.PROVIDED) and (other.mode == ValueSpec.PROVIDED):
			if self.value != other.value:
				raise ArgumentError("Conflicting provided values.")
		# ...otherwise the left has advantage
		if (other.mode == ValueSpec.PROVIDED):
			return other
		else:
			return self
	
	def __and__(self, tspec):
		if self.mode == ValueSpec.REQUIRED:
			return self
		if tspec.isValid(self.value):
			return self
		if self.mode == ValueSpec.OPTIONAL:
			return ValueSpec()
		else:
			raise TypeError("'{0}' does not satisfy the specification '{1}'.".format(self.value, tspec))


class ArgumentSpec(object):
	"""An argument specification."""

	def __init__(self, description, tspec=None, vspec=None, **kwargs):
		if 'type' in kwargs:
			if not isinstance(kwargs['type'], list):
				kwargs['type'] = [kwargs['type']]
		if 'fixed' in kwargs:
			if kwargs['fixed'] is None:
				kwargs['none'] = True
		elif 'default' in kwargs:
			if kwargs['default'] is None:
				kwargs['none'] = True
		self.description = description
		self.tspec = tspec or TypeSpec(**kwargs)
		self.vspec = (vspec or ValueSpec(**kwargs)) & self.tspec
	
	def __add__(self, other):
		tspec = self.tspec & other.tspec
		vspec = (self.vspec & other.tspec) + (other.vspec & self.tspec)
		return ArgumentSpec(self.description, tspec, vspec)
	
	def apply(self, args, key):
		"""Applies this specification to a given argument."""
		vspec = (key in args) and ValueSpec(fixed=args[key]) or ValueSpec()
		vspec &= self.tspec
		vspec += self.vspec
		if vspec.mode == ValueSpec.REQUIRED:
			raise ArgumentError("Required argument '{0}' not provided.".format(key))
		args[key] = vspec.value


MAGIC_ORIG = 'ph.objects.original'
MAGIC_SPEC = 'ph.objects.argspec'


class MetaObject(type):
	"""Metaclass for Object.
	"""

	def __new__(mcs, name, bases, dict_):
		if '__init__' in dict_:
			spec = {}
			calls = []
			def newinit(self, **kwargs):			# pylint: disable-msg=C0111
				args = Namespace(**kwargs)
				for key in spec:
					spec[key].apply(args, key)
				for call in calls:
					call(self, args)
			oldinit = dict_['__init__']
			newinit.__name__ = oldinit.__name__		# pylint: disable-msg=W0622
			newinit.__doc__ = oldinit.__doc__		# pylint: disable-msg=W0622
			newinit.func_dict[MAGIC_SPEC] = oldinit.func_dict.get(MAGIC_SPEC, {})
			newinit.func_dict[MAGIC_ORIG] = oldinit
			dict_['__init__'] = newinit
		class_ = type.__new__(mcs, name, bases, dict_)
		if '__init__' in dict_:
			for parent in class_.__mro__:
				init = parent.__dict__.get('__init__')
				if (init is None) or not hasattr(init, 'func_dict'):
					continue
				calls.append(init.func_dict.get(MAGIC_ORIG, init))
				plus = init.func_dict.get(MAGIC_SPEC, {})
				for key in plus:
					spec[key] = (key in spec) and (spec[key] + plus[key]) or plus[key]
			calls.reverse()
		return class_


class Object(object):
	"""A better replacement for 'object'.
	Supports super() constructor chaining.
	"""

	__metaclass__ = MetaObject


class Argument(object):
	"""Decorator. Describes an argument."""

	def __init__(self, name, desc='', **kwargs):
		self.name = name
		self.desc = desc
		self.args = kwargs
	
	def __call__(self, function):
		if hasattr(function, 'func_dict'):
			spec = function.func_dict.get(MAGIC_SPEC, {})
			if self.name in spec:
				raise ArgumentError("Duplicate specification for argument {0}.".format(self.name))
			spec[self.name] = ArgumentSpec(description=self.desc, **self.args)
			function.func_dict[MAGIC_SPEC] = spec
		return function
