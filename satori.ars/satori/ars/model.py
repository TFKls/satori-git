# vim:ts=4:sts=4:sw=4:expandtab
"""An in-memory model for an exported service.
"""


import types

from satori.objects import Object, Argument, ArgumentError
from satori.ars.naming import NamedObject


__all__ = (
    'Boolean', 'Int16', 'Int32', 'Int64', 'String', 'Void',
    'Field', 'ListType', 'MapType', 'SetType', 'Structure', 'TypeAlias',
    'Parameter', 'Procedure', 'Contract'
)


class Element(Object):
    """Abstract. Base for ARS model elements.
    """
    pass


class Type(Element):
    """Abstract. Base for ARS data types.
    """

    def isSimple(self):
        """Checks whether this Type is simple.
        """
        raise NotImplementedError()


class AtomicType(Type):
    """A Type without (visible) internal structure.
    """

    def isSimple(self):
        return True


Boolean = AtomicType()
Int8 = AtomicType()
Int16 = AtomicType()
Int32 = AtomicType()
Int64 = AtomicType()
Float = AtomicType()
String = AtomicType()
Void = AtomicType()


class ListType(Type):
    """A List Type.
    """

    @Argument('element_type', type=Type)
    def __init__(self, element_type):
        self.element_type = element_type

    def isSimple(self):
        return False

    def __str__(self):
        return 'List<'+str(self.element_type)+'>'


class SetType(Type):
    """A Set Type.
    """

    @Argument('element_type', type=Type)
    def __init__(self, element_type):
        self.element_type = element_type

    def isSimple(self):
        return False

    def __str__(self):
        return 'Set<'+str(self.element_type)+'>'


class MapType(Type):
    """A Map Type.
    """

    @Argument('key_type', type=Type)
    @Argument('value_type', type=Type)
    def __init__(self, key_type, value_type):
        self.key_type = key_type
        self.value_type = value_type

    def isSimple(self):
        return False

    def __str__(self):
        return 'Map<'+str(self.key_type)+','+str(self.value_type)+'>'


class NamedType(Type, NamedObject):
    """Abstract. A Type with a Name.
    """

    def isSimple(self):
        """Checks whether this Type is simple.
        """
        raise NotImplementedError()


class TypeAlias(NamedType):
    """A named alias for a Type.
    """

    @Argument('target_type', type=Type)
    def __init__(self, target_type):
        self.target_type = target_type

    def isSimple(self):
        return self.target_type.isSimple()


class NamedTuple(Object):

    def __init__(self):
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
    
    def __getitem__(self, index):
        return self.items[index]


class Field(Element, NamedObject):

    @Argument('type', type=Type)
    @Argument('optional', type=bool, default=False)
    def __init__(self, type, optional):                        # pylint: disable-msg=W0622
        self.type = type
        self.optional = optional


class Structure(NamedType):

    def __init__(self):
        self.fields = NamedTuple()

    def isSimple(self):
        return False

    def addField(self, field=None, **kwargs):
        if field is None:
            field = Field(**kwargs)
        self.fields.add(field)


class Parameter(Element, NamedObject):

    @Argument('type', type=Type)
    @Argument('optional', type=bool, default=False)
    @Argument('default', default=None)
    def __init__(self, type, optional, default):               # pylint: disable-msg=W0622
        self.type = type
        self.optional = optional
        self.default = default


class Procedure(Element, NamedObject):

    EX2STRING = lambda ex: str(ex)                             # pylint: disable-msg=W0108

    @Argument('return_type', type=Type, default=Void)
    @Argument('implementation', type=(types.FunctionType,None), default=None)
    @Argument('error_type', type=Type, default=String)
    @Argument('error_transform', type=types.FunctionType, default=EX2STRING)
    def __init__(self, return_type, implementation, error_type, error_transform):
        self.return_type = return_type
        self.implementation = implementation
        self.error_type = error_type
        self.error_transform = error_transform
        self.parameters = NamedTuple()

    def addParameter(self, parameter=None, **kwargs):
        if parameter is None:
            parameter = Parameter(**kwargs)
        self.parameters.add(parameter)


class Contract(Element, NamedObject):

    def __init__(self):
        self.procedures = NamedTuple()

    def addProcedure(self, procedure=None, **kwargs):
        if procedure is None:
            procedure = Procedure(**kwargs)
        self.procedures.add(procedure)
