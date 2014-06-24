# vim:ts=4:sts=4:sw=4:expandtab
"""An in-memory model for an exported service.
"""

import six

from datetime       import datetime
from time           import mktime
from types          import FunctionType
from satori.objects import Argument, DispatchOn

NoneType = type(None)


class ArsElement(object):
    """Abstract. A base class for ARS model elements.
    """

    pass


class ArsNamedElement(ArsElement):
    """Abstract. A base class for ARS model elements that have a name.
    """

    @Argument('name', type=str)
    def __init__(self, name):
        super(ArsNamedElement, self).__init__()
        self.name = name

    def __str__(self):
        return self.__class__.__name__ + ':' + self.name


class ArsType(ArsElement):
    """Abstract. A base class for ARS data types.
    """

    def __init__(self):
        super(ArsType, self).__init__()
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


class ArsNamedType(ArsNamedElement, ArsType):
    """Abstract. An ArsType that has a name.
    """

    def __init__(self, name):
        super(ArsNamedType, self).__init__(name)


class ArsAtomicType(ArsNamedType):
    """An ArsType without (visible) internal structure.
    """

    def __init__(self, name):
        super(ArsAtomicType, self).__init__(name)

ArsBoolean = ArsAtomicType(name='ArsBoolean')
ArsInt8 = ArsAtomicType(name='ArsInt8')
ArsInt16 = ArsAtomicType(name='ArsInt16')
ArsInt32 = ArsAtomicType(name='ArsInt32')
ArsInt64 = ArsAtomicType(name='ArsInt64')
ArsFloat = ArsAtomicType(name='ArsFloat')
ArsVoid = ArsAtomicType(name='ArsVoid')
ArsBinary = ArsAtomicType(name='ArsBinary')


class ArsStringType(ArsAtomicType):
    def __init__(self, name):
        super(ArsStringType, self).__init__(name)

    def do_needs_conversion(self):
        return True

    def do_convert_to_ars(self, value):
        if isinstance(value, six.text_type):
            return value.encode('utf-8')
        else:
            return value

    def do_convert_from_ars(self, value):
        if isinstance(value, six.binary_type):
            return six.text_type(value, 'utf-8')
        else:
            return value

ArsString = ArsStringType(name='ArsString')


class ArsTypeAlias(ArsNamedType):
    """A named alias for an ArsType.
    """

    @Argument('target_type', type=ArsType)
    def __init__(self, name, target_type):
        super(ArsTypeAlias, self).__init__(name)
        self.target_type = target_type

    def do_needs_conversion(self):
        return self.target_type.needs_conversion()

    def do_convert_to_ars(self, value):
        return self.target_type.convert_to_ars(value)

    def do_convert_from_ars(self, value):
        return self.target_type.convert_from_ars(value)


class ArsList(ArsType):
    """An ArsType representing a list.
    """

    @Argument('element_type', type=ArsType)
    def __init__(self, element_type):
        super(ArsList, self).__init__()
        self.element_type = element_type

    def __str__(self):
        return 'ArsList<'+str(self.element_type)+'>'

    def do_needs_conversion(self):
        return self.element_type.needs_conversion()

    def do_convert_to_ars(self, value):
        return [self.element_type.convert_to_ars(elem) for elem in value]

    def do_convert_from_ars(self, value):
        return [self.element_type.convert_from_ars(elem) for elem in value]


class ArsSet(ArsType):
    """An ArsType representing set.
    """

    @Argument('element_type', type=ArsType)
    def __init__(self, element_type):
        super(ArsSet, self).__init__()
        self.element_type = element_type

    def __str__(self):
        return 'ArsSet<'+str(self.element_type)+'>'

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


class ArsMap(ArsType):
    """An ArsType representing a key-value mapping.
    """

    @Argument('key_type', type=ArsType)
    @Argument('value_type', type=ArsType)
    def __init__(self, key_type, value_type):
        super(ArsMap, self).__init__()
        self.key_type = key_type
        self.value_type = value_type

    def __str__(self):
        return 'ArsMap<'+str(self.key_type)+','+str(self.value_type)+'>'

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


class ArsNamedTuple(object):
    """A list of ArsNamedElements that have unique names. Something like an ordered dictionary.
    """

    def __init__(self):
        super(ArsNamedTuple, self).__init__()
        self.names = dict()
        self.items = list()

    @Argument('item', type=ArsNamedElement)
    def append(self, item):
        if item.name in self:
            if self[item.name] == item:
                return
            else:
                raise ValueError('Duplicate item name')
        self.names[item.name] = item
        self.items.append(item)

    def extend(self, tuple):
        items = list()
        for item in tuple:
            if item.name in self:
                if self[item.name] == item:
                    pass
                else:
                    raise ValueError('Duplicate item name')
            else:
                items.append(item)
        for item in items:
            self.append(item)

    def __contains__(self, elem):
        if isinstance(elem, six.string_types):
            return elem in self.names
        elif isinstance(elem, ArsNamedElement):
            return (elem.name in self.names) and (self.names[elem.name] == elem)
        else:
            return False

    def __iter__(self):
        return self.items.__iter__()

    def __len__(self):
        return self.items.__len__()

    def __getitem__(self, index):
        if isinstance(index, six.string_types):
            return self.names[index]
        elif isinstance(index, int):
            return self.items[index]
        else:
            raise TypeError('ArsNamedTuple index should be int or str')

    def __str__(self):
        return 'ArsNamedTuple[' + ','.join(str(item) for item in self.items) + ']'


class ArsField(ArsNamedElement):
    """A single field of an ArsStructure.
    """

    @Argument('type', type=ArsType)
    @Argument('optional', type=bool)
    def __init__(self, name, type, optional=False):                        # pylint: disable-msg=W0622
        super(ArsField, self).__init__(name)
        self.type = type
        self.optional = optional


class ArsStructureBase(object):
    def __init__(self, dict_=None, **kwargs):
        super(ArsStructureBase, self).__init__()
        if dict_:
            kwargs.update(dict_)
        for field_name in self._ars_type.fields.names:
            if field_name in kwargs:
                setattr(self, field_name, kwargs.pop(field_name))
            else:
                setattr(self, field_name, None)
        if kwargs:
            raise TypeError('__init__() got an unexpected keyword argument \'{0}\''.format(kwargs.keys()[0]))
    
    @classmethod
    def ars_type(cls):
        return cls._ars_type

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __delitem__(self, key):
        return delattr(self, key)

    def __contains__(self, key):
        return hasattr(self, key)


class ArsStructure(ArsNamedType):
    """An ArsType that represents a named structure.
    """

    @Argument('base_index', type=int)
    def __init__(self, name, base_index=1):
        super(ArsStructure, self).__init__(name)
        self.fields = ArsNamedTuple()
        self.base_index = base_index

    @Argument('field', type=ArsField)
    def add_field(self, field=None, **kwargs):
        if field is None:
            field = ArsField(**kwargs)
        self.fields.append(field)

    def do_needs_conversion(self):
        return True
#        return any(field.type.needs_conversion() for field in self.fields.items)

    def do_convert_to_ars(self, value):
        if isinstance(value, dict):
            value = self.get_class()(value)

        for field in self.fields.items:
            if hasattr(value, field.name) and field.type.needs_conversion():
                setattr(value, field.name, field.type.convert_to_ars(getattr(value, field.name)))

        return value

    def do_convert_from_ars(self, value):
        for field in self.fields.items:
            if hasattr(value, field.name) and field.type.needs_conversion():
                setattr(value, field.name, field.type.convert_from_ars(getattr(value, field.name)))

        return value

    def get_class(self):
        if not hasattr(self, '_class'):
            self._class = type(self.name, (ArsStructureBase,), {'_ars_type': self})
        return self._class


class ArsParameter(ArsField):
    """A single parameter of ArsProcedure.
    """

    def __init__(self, name, type, optional=False):               # pylint: disable-msg=W0622
        super(ArsParameter, self).__init__(name, type, optional)


class ArsProcedure(ArsNamedElement):
    """A procedure that can be remotely called.
    """

    @Argument('return_type', type=ArsType)
    @Argument('implementation', type=(FunctionType,NoneType))
    def __init__(self, name, return_type, implementation=None):
        super(ArsProcedure, self).__init__(name)
        self.return_type = return_type
        self.implementation = implementation
        self.parameters = ArsNamedTuple()
        self.exception_types = []

        self.parameters_struct = ArsStructure(name + '_args')
        self.results_struct = ArsStructure(name + '_result', 0)
        self.results_struct.add_field(name='result', type=return_type, optional=True)

    @Argument('parameter', type=ArsParameter)
    def add_parameter(self, parameter=None, **kwargs):
        if parameter is None:
            parameter = ArsParameter(**kwargs)
        self.parameters.append(parameter)
        self.parameters_struct.add_field(parameter)

    def add_exception(self, exception_type):
        self.exception_types.append(exception_type)
        self.results_struct.add_field(name='error'+str(len(self.exception_types)), type=exception_type, optional=True)


class ArsExceptionBase(Exception):
    def __init__(self, dict_=None, **kwargs):
        super(ArsExceptionBase, self).__init__()
        if dict_:
            kwargs.update(dict_)
        for field_name in self._ars_type.fields.names:
            if field_name in kwargs:
                setattr(self, field_name, kwargs.pop(field_name))
            else:
                setattr(self, field_name, None)
        if kwargs:
            raise TypeError('__init__() got an unexpected keyword argument \'{0}\''.format(kwargs.keys()[0]))

    def __str__(self):
        if ('message' in self._ars_type.fields) and (self.message is not None):
            return self.message
        else:
            return ', '.join(getattr(self, field_name) for field_name in self._ars_type.fields.names if getattr(self, field_name) is not None)

    @classmethod
    def ars_type(cls):
        return cls._ars_type


class ArsException(ArsStructure):
    def get_class(self):
        if not hasattr(self, '_class'):
            self._class = type(self.name, (ArsExceptionBase,), {'_ars_type': self})
        return self._class


class ArsService(ArsNamedElement):
    """A group of ArsProcedures.
    """

    def __init__(self, name, base=None):
        super(ArsService, self).__init__(name)
        self.base = base
        self.procedures = ArsNamedTuple()

    @Argument('procedure', type=ArsProcedure)
    def add_procedure(self, procedure=None, **kwargs):
        if procedure is None:
            procedure = ArsProcedure(**kwargs)
        self.procedures.append(procedure)


class ArsConstant(ArsNamedElement):
    """An element with a constant value.
    """

    @Argument('type', type=ArsType)
    def __init__(self, name, type, value):
        super(ArsConstant, self).__init__(name)
        self.type = type
        self.value = value


class ArsInterface(ArsElement):
    """A group of ArsNamedTypes, ArsConstants and ArsServices.
    """

    def __init__(self):
        self.types = ArsNamedTuple()
        self.constants = ArsNamedTuple()
        self.services = ArsNamedTuple()

    def add_type(self, type):
        if isinstance(type, ArsAtomicType):
        	pass
        elif isinstance(type, ArsTypeAlias):
            if type not in self.types:
                self.add_type(type.target_type)
                self.types.append(type)
        elif isinstance(type, ArsList):
            self.add_type(type.element_type)
        elif isinstance(type, ArsSet):
            self.add_type(type.element_type)
        elif isinstance(type, ArsMap):
            self.add_type(type.key_type)
            self.add_type(type.value_type)
        elif isinstance(type, ArsStructure):
            if type not in self.types:
                for field in type.fields:
                    self.add_type(field.type)
                self.types.append(type)
        else:
            raise TypeError('Unknown ArsType type: {0}'.format(type.__class__.__name__))

    def add_constant(self, constant=None, **kwargs):
        if constant is None:
            constant = ArsConstant(**kwargs)
        self.add_type(constant.type)
        self.constants.append(constant)

    def add_service(self, service):
        if service.base:
            self.add_service(service.base)
        for procedure in service.procedures:
            self.add_type(procedure.return_type)
            for parameter in procedure.parameters:
                self.add_type(parameter.type)
            for exception in procedure.exception_types:
                self.add_type(exception)
        self.services.append(service)

    @DispatchOn(type=ArsAtomicType)
    def deepcopy_type(self, type, new_interface):
        return type

    @DispatchOn(type=ArsNamedType)
    def deepcopy_type(self, type, new_interface):
        return new_interface.types[type.name]

    @DispatchOn(type=ArsList)
    def deepcopy_type(self, type, new_interface):
        return ArsList(element_type=self.deepcopy_type(type.element_type, new_interface))

    @DispatchOn(type=ArsSet)
    def deepcopy_type(self, type, new_interface):
        return ArsSet(element_type=self.deepcopy_type(type.element_type, new_interface))

    @DispatchOn(type=ArsMap)
    def deepcopy_type(self, type, new_interface):
        return ArsMap(key_type=self.deepcopy_type(type.key_type, new_interface), value_type=self.deepcopy_type(type.value_type, new_interface))

    @DispatchOn(type=ArsTypeAlias)
    def deepcopy_type_first(self, type, new_interface):
        return ArsTypeAlias(name=type.name, target_type=self.deepcopy_type(type.target_type, new_interface))

    @DispatchOn(type=ArsStructure)
    def deepcopy_type_first(self, type, new_interface):
        ret = ArsStructure(name=type.name, base_index=type.base_index)
        for field in type.fields:
            ret.add_field(name=field.name, type=self.deepcopy_type(field.type, new_interface), optional=field.optional)
        return ret

    @DispatchOn(type=ArsException)
    def deepcopy_type_first(self, type, new_interface):
        ret = ArsException(name=type.name, base_index=type.base_index)
        for field in type.fields:
            ret.add_field(name=field.name, type=self.deepcopy_type(field.type, new_interface), optional=field.optional)
        return ret

    def deepcopy(self):
        ret = ArsInterface()

        for type in self.types:
            ret.types.append(self.deepcopy_type_first(type, ret))

        for constant in self.constants:
            ret.constants.append(ArsConstant(type=self.deepcopy_type(constant.type, ret), value=type.value))

        for service in self.services:
            if service.base:
                ret_service = ArsService(name=service.name, base=ret.services[service.base.name])
            else:
                ret_service = ArsService(name=service.name)
            for procedure in service.procedures:
                ret_procedure = ArsProcedure(name=procedure.name, return_type=self.deepcopy_type(procedure.return_type, ret), implementation=procedure.implementation)
                for parameter in procedure.parameters:
                    ret_procedure.add_parameter(name=parameter.name, type=self.deepcopy_type(parameter.type, ret), optional=parameter.optional)
                for exception in procedure.exception_types:
                    ret_procedure.add_exception(self.deepcopy_type(exception))
                ret_service.add_procedure(ret_procedure)
            ret.services.append(ret_service)

        return ret


# additional type specialization

class ArsDateTime(ArsTypeAlias):
    def __init__(self, ):
        super(ArsDateTime, self).__init__(name='DateTime', target_type=ArsInt64)

    def do_needs_conversion(self):
        return True

    def do_convert_to_ars(self, value):
        return long(mktime(value.timetuple()))

    def do_convert_from_ars(self, value):
        return datetime.fromtimestamp(value)


ArsDateTime = ArsDateTime()


__all__ = [name for name in globals().keys() if name.startswith('Ars')]

