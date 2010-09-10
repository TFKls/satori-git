# vim:ts=4:sts=4:sw=4:expandtab
"""An in-memory model for an exported service.
"""

import types
from satori.objects import Object, Argument, ArgumentError, DispatchOn


__all__ = (
    'Boolean', 'Int16', 'Int32', 'Int64', 'String', 'Void',
    'Field', 'ListType', 'MapType', 'SetType', 'Structure', 'TypeAlias',
    'Parameter', 'Procedure', 'Contract',
    'NamedTuple', 'namedTypes'
)


class Element(object):
    """Abstract. A base class for ARS model elements.
    """

    pass


class NamedElement(Element):
    """Abstract. A base class for ARS model elements that have a name.
    """

    @Argument('name', type=str)
    def __init__(self, name):
        super(NamedElement, self).__init__()
        self.name = name

    def __str__(self):
        return self.__class__.__name__ + ':' + self.name


class Type(Element):
    """Abstract. A base class for ARS data types.
    """
    
    def __init__(self):
        self.converter = None

    def do_needs_conversion(self):
        return False

    def do_convert_to_ars(self, value):
        return value

    def do_convert_from_ars(self, value):
        return value

    def needs_conversion(self):
        if self.converter is not None:
            return self.converter.needs_conversion()
        else:
            return self.do_needs_conversion()

    def convert_to_ars(self, value):
        if value is None:
            return None
        
        if not self.needs_conversion():
            return value

        if self.converter is not None:
            return self.converter.convert_to_ars(value)
        else:
            return self.do_convert_to_ars(value)

    def convert_from_ars(self, value):
        if value is None:
            return None
        
        if not self.needs_conversion():
            return value

        if self.converter is not None:
            return self.converter.convert_from_ars(value)
        else:
            return self.do_convert_from_ars(value)


class NamedType(NamedElement, Type):
    """Abstract. A Type that has a name.
    """

    def __init__(self, name):
        super(NamedType, self).__init__(name)


class AtomicType(NamedType):
    """A Type without (visible) internal structure.
    """

    def __init__(self, name):
        super(AtomicType, self).__init__(name)


Boolean = AtomicType(name='Boolean')
Int8 = AtomicType(name='Int8')
Int16 = AtomicType(name='Int16')
Int32 = AtomicType(name='Int32')
Int64 = AtomicType(name='Int64')
Float = AtomicType(name='Float')
String = AtomicType(name='String')
Void = AtomicType(name='Void')


class TypeAlias(NamedType):
    """A named alias for a Type.
    """

    @Argument('target_type', type=Type)
    def __init__(self, name, target_type):
        super(TypeAlias, self).__init__(name)
        self.target_type = target_type


class ListType(Type):
    """A List Type.
    """

    @Argument('element_type', type=Type)
    def __init__(self, element_type):
        super(ListType, self).__init__()
        self.element_type = element_type

    def __str__(self):
        return 'List<'+str(self.element_type)+'>'

    def do_needs_conversion(self):
        return self.element_type.needs_conversion()

    def do_convert_to_ars(self, value):
        return [self.element_type.convert_to_ars(elem) for elem in value]

    def do_convert_from_ars(self, value):
        return [self.element_type.convert_from_ars(elem) for elem in value]


class SetType(Type):
    """A Set Type.
    """

    @Argument('element_type', type=Type)
    def __init__(self, element_type):
        super(SetType, self).__init__()
        self.element_type = element_type

    def __str__(self):
        return 'Set<'+str(self.element_type)+'>'

    def do_needs_conversion(self):
        return self.element_type.needs_conversion()

    def do_convert_to_ars(self, value):
        new_value = set()
        for elem in value:
            new_value.add(self.element_type.convert_to_ars(elem))
        return new_value

    def do_convert_from_ars(self, value):
        new_value = set()
        for elem in value:
            new_value.add(self.element_type.convert_from_ars(elem))
        return new_value


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

    def do_needs_conversion(self):
        return self.key_type.needs_conversion() or self.value_type.needs_conversion()

    def do_convert_to_ars(self, value):
        new_value = dict()
        for (key, elem) in value.iteritems():
            new_value[self.key_type.convert_to_ars(key)] = self.value_type.convert_to_ars(elem)
        return new_value

    def do_convert_from_ars(self, value):
        new_value = dict()
        for (key, elem) in value.iteritems():
            new_value[self.key_type.convert_from_ars(key)] = self.value_type.convert_from_ars(elem)
        return new_value


class NamedTuple(object):
    """A list of NamedElements that have unique names.
    """

    def __init__(self):
        super(NamedTuple, self).__init__()
        self.names = dict()
        self.items = list()
    
    @Argument('item', type=NamedElement)
    def append(self, item):
        if item.name in self:
            if self[item.name] == item:
                return
            else:
                raise ArgumentError("duplicate item name")
        self.names[item.name] = item
        self.items.append(item)

    def extend(self, tuple):
        items = list()
        for item in tuple:
            if item.name in self:
                if self[item.name] == item:
                    pass
                else:
                    raise ArgumentError("duplicate item name")
            else:
                items.append(item)
        for item in items:
            self.append(item)

    def __contains__(self, elem):
        return elem in self.names

    def __iter__(self):
        return self.items.__iter__()

    def __len__(self):
        return self.items.__len__()
    
    def __getitem__(self, index):
        if isinstance(index, str):
            return self.names[index]
        else:
            return self.items[index]

    def __str__(self):
        return 'NamedTuple[' + ','.join(str(item) for item in self.items) + ']'


class Field(NamedElement):
    """A single field of Structure.
    """


    @Argument('type', type=Type)
    @Argument('optional', type=bool)
    def __init__(self, name, type, optional=False):                        # pylint: disable-msg=W0622
        super(Field, self).__init__(name)
        self.type = type
        self.optional = optional
    

class Structure(NamedType):

    def __init__(self, name, base=1):
        super(Structure, self).__init__(name)
        self.fields = NamedTuple()
        self.base = base

    def add_field(self, field=None, **kwargs):
        if field is None:
            field = Field(**kwargs)
        self.fields.append(field)
    
    def do_needs_conversion(self):
        return any(field.type.needs_conversion() for field in self.fields.items)

    def do_convert_to_ars(self, value):
        new_value = {}
        for field in self.fields.items:
            if field.name in value:
                if field.type.needs_conversion():
                    new_value[field.name] = field.type.convert_to_ars(value[field.name])
                else:
                    new_value[field.name] = value[field.name]

        return new_value

    def do_convert_from_ars(self, value):
        new_value = {}
        for field in self.fields.items:
            if field.name in value:
                if field.type.needs_conversion():
                    new_value[field.name] = field.type.convert_from_ars(value[field.name])
                else:
                    new_value[field.name] = value[field.name]

        return new_value


class Parameter(Field):

    def __init__(self, name, type, optional=False, default=None):               # pylint: disable-msg=W0622
        super(Parameter, self).__init__(name, type, optional)
        self.default = default


class Procedure(NamedElement):

    @Argument('return_type', type=Type)
    @Argument('implementation', type=(types.FunctionType,None))
    def __init__(self, name, return_type=Void, implementation=None):
        super(Procedure, self).__init__(name)
        self.return_type = return_type
        self.implementation = implementation
        self.parameters = NamedTuple()
        self.exception_types = []

        self.parameters_struct = Structure(name + '_args')
        self.results_struct = Structure(name + '_result', 0)
        self.results_struct.add_field(name='result', type=return_type, optional=True)

    def add_parameter(self, parameter=None, **kwargs):
        if parameter is None:
            parameter = Parameter(**kwargs)
        self.parameters.append(parameter)
        self.parameters_struct.add_field(parameter)

    def add_exception(self, exception_type):
        self.exception_types.append(exception_type)
        self.results_struct.add_field(name='error', type=exception_type, optional=True)

class Exception(Structure):
    pass

class Contract(NamedElement):

    def __init__(self, name, base=None):
        super(Contract, self).__init__(name)
        self.base = base
        self.procedures = NamedTuple()

    def add_procedure(self, procedure=None, **kwargs):
        if procedure is None:
            procedure = Procedure(**kwargs)
        self.procedures.append(procedure)


@DispatchOn(item=AtomicType)
def namedTypes(item):
    nt = NamedTuple()
    nt.append(item)
    return nt

@DispatchOn(item=TypeAlias)
def namedTypes(item):
    nt = namedTypes(item.target_type)
    nt.append(item)
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
    nt.append(item)
    return nt

@DispatchOn(item=Parameter)
def namedTypes(item):
    return namedTypes(item.type)

@DispatchOn(item=Procedure)
def namedTypes(item):
    nt = namedTypes(item.return_type)
    for parameter in item.parameters:
        nt.extend(namedTypes(parameter))
    for exception_type in item.exception_types:
        nt.extend(namedTypes(exception_type))
    return nt

@DispatchOn(item=Contract)
def namedTypes(item):
    nt = NamedTuple()
    if item.base:
        nt.extend(namedTypes(item.base))
    for procedure in item.procedures:
        nt.extend(namedTypes(procedure))
    return nt


@DispatchOn(item=types.NoneType)
def ars_deepcopy(item, named):
    return None

@DispatchOn(item=AtomicType)
def ars_deepcopy(item, named):
    return item

@DispatchOn(item=ListType)
def ars_deepcopy(item, named):
    return ListType(element_type=ars_deepcopy(item.element_type, named))

@DispatchOn(item=SetType)
def ars_deepcopy(item, named):
    return SetType(element_type=ars_deepcopy(item.element_type, named))

@DispatchOn(item=MapType)
def ars_deepcopy(item, named):
    return MapType(key_type=ars_deepcopy(item.key_type, named), value_type=ars_deepcopy(item.value_type, named))

@DispatchOn(item=TypeAlias)
def ars_deepcopy(item, named):
    if item.name in named:
    	return named[item.name]
    ret = TypeAlias(name=item.name, target_type=ars_deepcopy(item.target_type, named))
    named.append(ret)
    return ret

@DispatchOn(item=Field)
def ars_deepcopy(item, named):
    return Field(name=item.name, type=ars_deepcopy(item.type, named), optional=item.optional)

@DispatchOn(item=Structure)
def ars_deepcopy(item, named):
    if item.name in named:
    	return named[item.name]
    ret = Structure(name=item.name, base=item.base)
    for field in item.fields:
        ret.add_field(ars_deepcopy(field, named))
    named.append(ret)
    return ret

@DispatchOn(item=Exception)
def ars_deepcopy(item, named):
    if item.name in named:
    	return named[item.name]
    ret = Exception(name=item.name, base=item.base)
    for field in item.fields:
        ret.add_field(ars_deepcopy(field, named))
    named.append(ret)
    return ret

@DispatchOn(item=Parameter)
def ars_deepcopy(item, named):
    return Parameter(name=item.name, type=ars_deepcopy(item.type, named), optional=item.optional, default=item.default)

@DispatchOn(item=Procedure)
def ars_deepcopy(item, named):
    ret = Procedure(name=item.name, return_type=ars_deepcopy(item.return_type, named), implementation=item.implementation)
    for parameter in item.parameters:
        ret.add_parameter(ars_deepcopy(parameter, named))
    for exception in item.exception_types:
        ret.add_exception(ars_deepcopy(exception, named))
    return ret

@DispatchOn(item=Contract)
def ars_deepcopy(item, named):
    if item.name in named:
    	return named[item.name]
    ret = Contract(name=item.name, base=ars_deepcopy(item.base, named))
    for procedure in item.procedures:
        ret.add_procedure(ars_deepcopy(procedure, named))
    named.append(ret)
    return ret

def ars_deepcopy_tuple(item):
    named = NamedTuple()
    ret = NamedTuple()
    for elem in item:
    	ret.append(ars_deepcopy(elem, named))
    return ret

