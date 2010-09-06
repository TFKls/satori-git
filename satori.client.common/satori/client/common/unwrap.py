from satori.ars.model import *
from satori.ars.wrapper import DateTimeTypeAlias, NullableArsStructure, String
from satori.ars import perf
from token_container import token_container

class UnwrapTypeAlias(TypeAlias):
    def __init__(self, cls):
        super(UnwrapTypeAlias, self).__init__(cls.__name__, Int64)
        self.cls = cls

    def do_needs_conversion(self):
        return True

    def do_convert_to_ars(self, value):
        return value._id

    def do_convert_from_ars(self, value):
        return self.cls(value)


def unwrap_proc(_proc):
    _procname = _proc.name
    _implementation = _proc.implementation
    _rettype = _proc.return_type
    _args = [(param.name, param.type, param.optional) for param in _proc.parameters.items]

    _token_type = None
    if _args and (_args[0][0] == 'token'):
        _token_type = _args.pop(0)[1]

    _arg_numbers = {}
    for i in range(len(_args)):
        _arg_numbers[_args[i][0]] = i

    def func(*args, **kwargs):
        perf.begin('wrap')
        newargs = []
        newkwargs = {}

        if _token_type is not None:
            newargs.append(_token_type.convert_to_ars(token_container.get_token()))

        if len(args) > len(_args):
            raise TypeError('{0}() takes at most {1} arguments ({2} given)'.format(_procname, len(_args), len(args)))

        for (i, value) in enumerate(args):
            argtype = _args[i][1]
            newargs.append(argtype.convert_to_ars(value))

        for (name, value) in kwargs.iteritems():
            if not name in _arg_numbers:
                raise TypeError('{0} got an unexpected keyword argument \'{1}\''.format(_procname, name))

            argtype = _args[_arg_numbers[name]][1]
            newkwargs[name] = argtype.convert_to_ars(value)

        ret = _implementation(*newargs, **newkwargs)
        ret = _rettype.convert_from_ars(ret)
        perf.end('wrap')
        return ret

    func.func_name = _procname

    if not (_args and (_args[0][0] == 'self')):
        func = staticmethod(func)

    return func

def unwrap_class(contract):
    class_name = contract.name
    class_bases = (object, )
    class_dict = {}

    for proc in contract.procedures:
        meth_name = proc.name.split('_', 1)[1]
        class_dict[meth_name] = unwrap_proc(proc)

    def __init__(self, id):
        self._id = id

    def __getattr__(self, name):
        if name == 'id':
            return self._id
        if (name[-4:] == '_get') or (name[-4:] == '_set'):
            raise AttributeError('\'{0}\' object has no attribute \'{1}\''.format(class_name, name))
        if hasattr(self, name + '_get'):
            return getattr(self, name + '_get')()
        else:
            raise AttributeError('\'{0}\' object has no attribute \'{1}\''.format(class_name, name))
        
    def __setattr__(self, name, value):
        if name[-4:] == '_set':
            return super(self.__class__, self).__setattr__(name, value)
        if hasattr(self, name + '_set'):
            return getattr(self, name + '_set')(value)
        else:
            return super(self.__class__, self).__setattr__(name, value)

    class_dict['__init__'] = __init__
    class_dict['__getattr__'] = __getattr__
    class_dict['__setattr__'] = __setattr__

    return type(class_name, class_bases, class_dict)

def unwrap_classes(contracts):
    types = NamedTuple()
    for contract in contracts:
        types.extend(namedTypes(contract))

    for type in types:
        if type.name == 'DateTime':
            type.converter = DateTimeTypeAlias
        if type.name == 'Token':
            type.converter = String
        if type is Structure:
            if type.fields and (type.fields[0].name == 'null_values'):
                newtype = NullableArsStructure(name=type.name)
                for field in type.fields[1:]:
                    newtype.add_field(field)
                type.converter = newtype

    classes = {}
    for contract in contracts:
        newcls = unwrap_class(contract)
        classes[contract.name] = newcls

        if (contract.name + 'Id') in types.names:
            types[contract.name + 'Id'].converter = UnwrapTypeAlias(newcls)

    return classes

