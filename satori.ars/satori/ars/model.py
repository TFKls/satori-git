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


class Element(object):
    pass


class NamedElement(Element):

    @Argument('name', type=Name)
    def __init__(self, name):
        super(NamedElement, self).__init__()
        self.name = name


class Type(Element):
    """Abstract. Base for ARS data types.
    """

    def needs_conversion(self):
        return False

    def convert_to_ars(self, value):
        return value

    def convert_from_ars(self, value):
        return value


class ListType(Type):
    """A List Type.
    """

    @Argument('element_type', type=Type)
    def __init__(self, element_type):
        super(ListType, self).__init__()
        self.element_type = element_type

    def __str__(self):
        return 'List<'+str(self.element_type)+'>'

    def needs_conversion(self):
        return self.element_type.needs_conversion()

    def convert_to_ars(self, value):
        if self.needs_conversion():
        	return [self.element_type.convert_to_ars(elem) for elem in value]
        else:
        	return value

    def convert_from_ars(self, value):
        if self.needs_conversion():
        	return [self.element_type.convert_from_ars(elem) for elem in value]
        else:
        	return value


class SetType(Type):
    """A Set Type.
    """

    @Argument('element_type', type=Type)
    def __init__(self, element_type):
        super(SetType, self).__init__()
        self.element_type = element_type

    def __str__(self):
        return 'Set<'+str(self.element_type)+'>'

    def needs_conversion(self):
        return self.element_type.needs_conversion()

    def convert_to_ars(self, value):
        if self.needs_conversion():
            new_value = set()
            for elem in value:
            	new_value.add(self.element_type.convert_to_ars(elem))
            return new_value
        else:
        	return value

    def convert_from_ars(self, value):
        if self.needs_conversion():
            new_value = set()
            for elem in value:
            	new_value.add(self.element_type.convert_from_ars(elem))
            return new_value
        else:
        	return value


class MapType(Type):
    """A Map Type.
    """

    @Argument('key_type', type=Type)
    @Argument('value_type', type=Type)
    def __init__(self, key_type, value_type):
        super(MapType, self).__init__()
        self.key_type = key_type
        self.value_type = value_type

    def __str__(self):
        return 'Map<'+str(self.key_type)+','+str(self.value_type)+'>'

    def needs_conversion(self):
        return self.key_type.needs_conversion() or self.value_type.needs_conversion()

    def convert_to_ars(self, value):
        if self.needs_conversion():
            new_value = dict()
            for (key, elem) in value.iteritems():
            	new_value[self.key_type.convert_to_ars(key)] = self.value_type.convert_to_ars(elem)
            return new_value
        else:
        	return value

    def convert_from_ars(self, value):
        if self.needs_conversion():
            new_value = dict()
            for (key, elem) in value.iteritems():
            	new_value[self.key_type.convert_from_ars(key)] = self.value_type.convert_from_ars(elem)
            return new_value
        else:
        	return value


class NamedType(Type):
    """Abstract. A Type with a Name.
    """

    @Argument('name', type=Name)
    def __init__(self, name):
        super(NamedType, self).__init__()
        self.name = name
    
    def __str__(self):
        return 'Type:' + NamingStyle.DEFAULT.format(self.name)


class AtomicType(NamedType):
    """A Type without (visible) internal structure.
    """

    def __init__(self, name):
        super(AtomicType, self).__init__(name)


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
    def __init__(self, name, target_type):
        super(TypeAlias, self).__init__(name)
        self.target_type = target_type


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


class Field(NamedElement):

    @Argument('type', type=Type)
    @Argument('optional', type=bool)
    def __init__(self, name, type, optional=False):                        # pylint: disable-msg=W0622
        super(Field, self).__init__(name)
        self.name = name
        self.type = type
        self.optional = optional
    
    def __str__(self):
        return 'Field:' + NamingStyle.DEFAULT.format(self.name)


class Structure(NamedType):

    def __init__(self, name):
        super(Structure, self).__init__(name)
        self.fields = NamedTuple()

    def addField(self, field=None, **kwargs):
        if field is None:
            field = Field(**kwargs)
        self.fields.add(field)
    
    def __str__(self):
        return 'Structue:' + NamingStyle.DEFAULT.format(self.name)

    def needs_conversion(self):
        return any(field.type.needs_conversion() for field in self.fields.items)

    def convert_to_ars(self, value):
        if self.needs_conversion():
        	new_value = {}
            for field in self.fields.items:
            	field_name = NamingStyle.PYTHON.format(field.name)
                if field_name in value:
                    if field.type.needs_conversion():
                    	new_value[field_name] = field.type.convert_to_ars(value[field_name])
                    else:
                    	new_value[field_name] = value[field_name]

            return new_value
        else:
        	return value

    def convert_from_ars(self, value):
        if self.needs_conversion():
        	new_value = {}
            for field in self.fields.items:
            	field_name = NamingStyle.PYTHON.format(field.name)
                if field_name in value:
                    if field.type.needs_conversion():
                    	new_value[field_name] = field.type.convert_from_ars(value[field_name])
                    else:
                    	new_value[field_name] = value[field_name]

            return new_value
        else:
        	return value


class Parameter(NamedElement):

    @Argument('type', type=Type)
    @Argument('optional', type=bool)
    def __init__(self, name, type, optional=False, default=None):               # pylint: disable-msg=W0622
        super(Parameter, self).__init__(name)
        self.type = type
        self.optional = optional
        self.default = default

    def __str__(self):
        return 'Parameter:' + NamingStyle.DEFAULT.format(self.name)


class Procedure(NamedElement):

    EX2STRING = lambda ex: str(ex)                             # pylint: disable-msg=W0108

    @Argument('return_type', type=Type)
    @Argument('implementation', type=(types.FunctionType,None))
    @Argument('error_type', type=Type)
    @Argument('error_transform', type=types.FunctionType)
    def __init__(self, name, return_type=Void, implementation=None, error_type=String, error_transform=EX2STRING):
        super(Procedure, self).__init__(name)
        self.return_type = return_type
        self.implementation = implementation
        self.error_type = error_type
        self.error_transform = error_transform
        self.parameters = NamedTuple()

    def addParameter(self, parameter=None, **kwargs):
        if parameter is None:
            parameter = Parameter(**kwargs)
        self.parameters.add(parameter)

    def __str__(self):
        return 'Procedure:' + NamingStyle.DEFAULT.format(self.name)


class Contract(NamedElement):

    def __init__(self, name):
        super(Contract, self).__init__(name)
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
