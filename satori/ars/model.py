"""
Defines the ARS service model.
"""


import types

from satori.ph import objects
from satori.ph.exceptions import ArgumentError
from satori.ars.naming import NamedObject


__all__ = (
	'Boolean', 'Int16', 'Int32', 'Int64', 'String',
	'TypeAlias', 'Structure',
	'Field', 'Argument', 'Error', 'Procedure', 'Contract'
)


class Element(objects.Object):
	"""Abstract. Base for ARS model elements.
	"""
	pass


class Type(Element):
	"""Abstract. Base for ARS data types.
	"""

	def isSimple(self):
		"""Checks whether this Type is simple.
		"""
		raise NotImplementedError


class AtomicType(Type):
	"""A Type without (visible) internal structure.
	"""

	def isSimple(self):
		return True


Boolean = AtomicType()
Int16 = AtomicType()
Int32 = AtomicType()
Int64 = AtomicType()
String = AtomicType()
Void = AtomicType()


class NamedType(Type, NamedObject):
	"""A Type with a Name.
	"""
	pass


class TypeAlias(NamedType):
	"""A named alias for a Type.
	"""

	@objects.Argument('targetType', type=Type)
	def __init__(self, kwargs):
		self.targetType = kwargs.targetType

	def isSimple(self):
		return self.targetType.isSimple()


class NamedTuple(objects.Object):

	def __init__(self, kwargs):
		self.names = set()
		self.items = list()

	def add(self, component):
		if component.name in self.names:
			raise ArgumentError("duplicate component name")
		self.names.add(component.name)
		self.items.append(component)

	def __iter__(self):
		return self.items.__iter__()

	def __len__(self):
		return self.items.__len__()


class Field(Element, NamedObject):

	@objects.Argument('type', type=Type)
	@objects.Argument('optional', type=bool, default=False)
	def __init__(self, kwargs):
		self.type = kwargs.type
		self.optional = kwargs.optional


class Structure(NamedType):

	def __init__(self, kwargs):
		self.fields = NamedTuple()

	def isSimple(self):
		return False

	def addField(self, field=None, **kwargs):
		if field is None:
			field = Field(**kwargs)
		self.fields.add(field)


class Argument(Element, NamedObject):

	@objects.Argument('type', type=Type)
	@objects.Argument('optional', type=bool, default=False)
	@objects.Argument('default', default=None)
	def __init__(self, kwargs):
		self.type = kwargs.type
		self.optional = kwargs.optional
		self.default = kwargs.default


class Error(Element, NamedObject):

	@objects.Argument('type', type=Type)
	def __init__(self, kwargs):
		self.type = kwargs.type


class Procedure(Element, NamedObject):

	@objects.Argument('returnType', type=Type, default=Void)
	@objects.Argument('implementation', type=types.FunctionType, default=None)
	def __init__(self, kwargs):
		self.returnType = kwargs.returnType
		self.implementation = kwargs.implementation
		self.arguments = NamedTuple()
		self.exceptions = NamedTuple()

	def addArgument(self, argument=None, **kwargs):
		if argument is None:
			argument = Argument(**kwargs)
		self.arguments.add(argument)

	def addException(self, exception=None, **kwargs):
		if exception is None:
			exception = Error(**kwargs)
		self.exceptions.add(exception)


class Contract(Element, NamedObject):

	def __init__(self, kwargs):
		self.procedures = {}

	def addProcedure(self, procedure=None, **kwargs):
		if procedure is None:
			procedure = Procedure(**kwargs)
		name = procedure.name.components[-1]
		if name in self.procedures:
			raise AttributeError("duplicate procedure '{0}'".format(procedure.name))
		self.procedures[name] = procedure
