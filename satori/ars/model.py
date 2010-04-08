# vim:ts=4:sts=4:sw=4:expandtab
"""An in-memory model for an exported service.
"""


import types

from satori.objects import Object, Argument, ArgumentError
from satori.ars.naming import NamedObject


__all__ = (
    'Boolean', 'Int16', 'Int32', 'Int64', 'String',
    'TypeAlias', 'Structure',
    'Field', 'Parameter', 'Procedure', 'Contract'
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
Int16 = AtomicType()
Int32 = AtomicType()
Int64 = AtomicType()
String = AtomicType()
Void = AtomicType()


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
    @Argument('implementation', type=types.FunctionType, default=None)
    @Argument('error_type', type=Type, default=String)
    @Argument('error_transform', type=types.FunctionType, default=EX2STRING)
    def __init__(self, return_type, implementation, error_type, error_transform):
        self.return_type = return_type
        self.implementation = implementation
        self.error_type = error_type
        self.error_transform = error_transform
        self.parameters = NamedTuple()

    def addParameter(self, argument=None, **kwargs):
        if argument is None:
            argument = Parameter(**kwargs)
        self.parameters.add(argument)


class Contract(Element, NamedObject):

    def __init__(self):
        self.procedures = {}

    def addProcedure(self, procedure=None, **kwargs):
        if procedure is None:
            procedure = Procedure(**kwargs)
        name = procedure.name.components[-1]
        if name in self.procedures:
            raise ArgumentError("duplicate procedure '{0}'".
                                        format(procedure.name))
        self.procedures[name] = procedure
