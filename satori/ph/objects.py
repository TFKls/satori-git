"""Useful additions to the standard Pyhton class hierarchy."""


__all__ = (
	'Object', 'Argument', 'ArgumentMode',
)


from satori.ph.exceptions import ArgumentError
from satori.ph.misc import Namespace


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
		desc = ""
		for type_ in self.type:
			if isinstance(type_, tuple):
				for option in type_:
					desc += option.__name__
					desc += " or "
				desc = desc[:-4]
			else:
				desc += type_.__name__
			desc += ", "
		if not self.none:
			desc += "not None, "
		desc = desc[:-2]
		return desc
	
	def isValid(self, value):
		"""Checks whether a given value meets this TypeSpec."""
		if value is None:
			return self.none
		for type_ in self.type:
			if not isinstance(value, type_):
				return False
		return True


class ArgumentMode(object):
	"""Enumeration. Modes for function arguments."""

	REQUIRED = 0
	OPTIONAL = 1
	PROVIDED = 2


class ValueSpec(object):
	"""An argument value specification."""

	def __init__(self, **kwargs):
		self.value = None
		self.mode = ArgumentMode.REQUIRED
		if 'default' in kwargs:
			self.value = kwargs['default']
			self.mode = ArgumentMode.OPTIONAL
		if 'fixed' in kwargs:
			self.value = kwargs['fixed']
			self.mode = ArgumentMode.PROVIDED
	
	def __str__(self):
		if self.mode == ArgumentMode.REQUIRED:
			return "required"
		if self.mode == ArgumentMode.OPTIONAL:
			return "optional, default = " + str(self.value)
		if self.mode == ArgumentMode.PROVIDED:
			return "fixed, value = " + str(self.value)
		raise Exception('this should NOT happen!')
	
	def __add__(self, other):
		# one witout a value always looses...
		if (self.mode == ArgumentMode.REQUIRED):
			return other
		if (other.mode == ArgumentMode.REQUIRED):
			return self
		# ...two strongmen agree or die...
		if (self.mode == ArgumentMode.PROVIDED) and (other.mode == ArgumentMode.PROVIDED):
			if self.value != other.value:
				raise ArgumentError("Conflicting provided values.")
		# ...otherwise the left has advantage
		if (other.mode == ArgumentMode.PROVIDED):
			return other
		else:
			return self
	
	def __and__(self, tspec):
		if self.mode == ArgumentMode.REQUIRED:
			return self
		if tspec.isValid(self.value):
			return self
		if self.mode == ArgumentMode.OPTIONAL:
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
	
	def __str__(self):
		tdesc = str(self.tspec)
		vdesc = str(self.vspec)
		if len(tdesc) > 0:
			return tdesc + ", " + vdesc
		else:
			return vdesc
	
	def __add__(self, other):
		tspec = self.tspec & other.tspec
		vspec = (self.vspec & other.tspec) + (other.vspec & self.tspec)
		return ArgumentSpec(self.description, tspec, vspec)
	
	def apply(self, args, key):
		"""Applies this specification to a given argument."""
		vspec = (key in args) and ValueSpec(fixed=args[key]) or ValueSpec()
		vspec &= self.tspec
		vspec += self.vspec
		if vspec.mode == ArgumentMode.REQUIRED:
			raise ArgumentError("Required argument '{0}' not provided.".format(key))
		args[key] = vspec.value
	
	mode = property(lambda self: self.vspec.mode)


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
