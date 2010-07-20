# vim:ts=4:sts=4:sw=4:expandtab
"""An in-memory model for an exported service.
"""


import types

from satori.objects import Object, Argument, ArgumentError, DispatchOn
from satori.ars.naming import Name, ClassName, NamedObject, NamingStyle


__all__ = (
    'Boolean', 'Int16', 'Int32', 'Int64', 'String', 'Void',
    'Field', 'ListType', 'MapType', 'SetType', 'Structure', 'TypeAlias',
    'Parameter', 'Procedure', 'Contract',
    'NamedTuple', 'namedTypes'
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


class AtomicType(NamedType):
    """A Type without (visible) internal structure.
    """

    def __init__(self):
        pass

    def __str__(self):
        return NamingStyle.DEFAULT.format(self.name)

    def isSimple(self):
        return True


Boolean = AtomicType(name=Name(ClassName('Boolean')))
Int8 = AtomicType(name=Name(ClassName('Int8')))
Int16 = AtomicType(name=Name(ClassName('Int16')))
Int32 = AtomicType(name=Name(ClassName('Int32')))
Int64 = AtomicType(name=Name(ClassName('Int64')))
Float = AtomicType(name=Name(ClassName('Float')))
String = AtomicType(name=Name(ClassName('String')))
Void = AtomicType(name=Name(ClassName('Void')))


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
        self.names = dict()
        self.items = list()
        self.DEFAULT = dict()
        self.PYTHON = dict()
        self.IDENTIFIER = dict()

    def add(self, component):
        if component.name in self.names:
            if self.names[component.name] == component:
            	return
            else:
                raise ArgumentError("duplicate component name")
        self.names[component.name] = component
        self.items.append(component)
        self.DEFAULT[NamingStyle.DEFAULT.format(component.name)] = component
        self.PYTHON[NamingStyle.PYTHON.format(component.name)] = component
        self.IDENTIFIER[NamingStyle.IDENTIFIER.format(component.name)] = component

    def extend(self, tuple):
        components = list()
        for component in tuple.items:
            if component.name in self.names:
                if self.names[component.name] == component:
                    pass
                else:
                    raise ArgumentError("duplicate component name")
            else:
            	components.append(component)
        for component in components:
            self.names[component.name] = component
            self.items.append(component)
            self.DEFAULT[NamingStyle.DEFAULT.format(component.name)] = component
            self.PYTHON[NamingStyle.PYTHON.format(component.name)] = component
            self.IDENTIFIER[NamingStyle.IDENTIFIER.format(component.name)] = component

    def update_prefix(self, arg):
        self.names = set()
        self.DEFAULT = dict()
        self.PYTHON = dict()
        self.IDENTIFIER = dict()
        for component in self.items:
            component.name = component.name.prefix(arg)
            self.names.add(component.name)
            self.DEFAULT[NamingStyle.DEFAULT.format(component.name)] = component
            self.PYTHON[NamingStyle.PYTHON.format(component.name)] = component
            self.IDENTIFIER[NamingStyle.IDENTIFIER.format(component.name)] = component

    def update_suffix(self, arg):
        self.names = set()
        self.DEFAULT = dict()
        self.PYTHON = dict()
        self.IDENTIFIER = dict()
        for component in self.items:
            component.name = component.name.suffix(arg)
            self.names.add(component.name)
            self.DEFAULT[NamingStyle.DEFAULT.format(component.name)] = component
            self.PYTHON[NamingStyle.PYTHON.format(component.name)] = component
            self.IDENTIFIER[NamingStyle.IDENTIFIER.format(component.name)] = component

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

@DispatchOn(item=AtomicType)
def namedTypes(item):
    nt = NamedTuple()
    nt.add(item)
    return nt
@DispatchOn(item=TypeAlias)
def namedTypes(item):
    nt = namedTypes(item.target_type)
    nt.add(item)
    return nt
@DispatchOn(item=ListType)
def namedTypes(item):
    return namedTypes(item.element_type)
@DispatchOn(item=MapType)
def namedTypes(item):
    nt = namedTypes(item.key_type)
    nt.extend(namedTypes(item.value_type))
    return nt
@DispatchOn(item=SetType)
def namedTypes(item):
    return namedTypes(item.element_type)
@DispatchOn(item=Field)
def namedTypes(item):
    return namedTypes(item.type)
@DispatchOn(item=Structure)
def namedTypes(item):
    nt = NamedTuple()
    for field in item.fields:
        nt.extend(namedTypes(field))
    nt.add(item)
    return nt
@DispatchOn(item=Parameter)
def namedTypes(item):
    return namedTypes(item.type)
@DispatchOn(item=Procedure)
def namedTypes(item):
    nt = namedTypes(item.return_type)
    nt.extend(namedTypes(item.error_type))
    for parameter in item.parameters:
    	nt.extend(namedTypes(parameter))
    return nt
@DispatchOn(item=Contract)
def namedTypes(item):
    nt = NamedTuple()
    for procedure in item.procedures:
    	nt.extend(namedTypes(procedure))
    return nt
