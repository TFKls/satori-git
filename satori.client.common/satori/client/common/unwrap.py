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

class UnwrapBase(object):
    def __init__(self, id, first=True):
        super(UnwrapBase, self).__init__()


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

def unwrap_class(contract, base, fields):
    class_name = contract.name
    class_dict = {}

    for proc in contract.procedures:
        meth_name = proc.name.split('_', 1)[1]
        class_dict[meth_name] = unwrap_proc(proc)

    if fields is not None:
        def __init__(self, id, first=True):
            super(new_class, self).__init__(id, False)
            if first:
                self._id = id
                self._struct = None

        def __getattr__(self, name):
            if name in fields:
                if self._struct is None:
                    self._struct = self.get_struct()
                if name in self._struct:
                    return self._struct[name]
                else:
                    # or raise error?
                    return None
            else:
                raise AttributeError('\'{0}\' object has no attribute \'{1}\''.format(class_name, name))
            
        def __setattr__(self, name, value):
            if name == 'id':
                raise Exception('Object id cannot be changed')

            if name in fields:
                self.set_struct({name: value})
                if self._struct is not None:
                    self._struct[name] = value
            else:
                return super(new_class, self).__setattr__(name, value)

        class_dict['__init__'] = __init__
        class_dict['__getattr__'] = __getattr__
        class_dict['__setattr__'] = __setattr__

    new_class = type(class_name, (base,), class_dict)
    return new_class


def unwrap_classes(contracts):
    types = NamedTuple()
    for contract in contracts:
        types.extend(namedTypes(contract))

    for type in types:
        if type.name == 'DateTime':
            type.converter = DateTimeTypeAlias()
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
        if contract.base:
            base = classes[contract.base.name]
        else:
            base = UnwrapBase

        if contract.name + 'Struct' in types.names:
            struct = types[contract.name + 'Struct']
            if isinstance(struct.converter, NullableArsStructure):
                fields = [field.name for field in struct.fields[1:]]
            else:
                fields = [field.name for field in struct.fields]
        else:
            fields = None
            
        newcls = unwrap_class(contract, base, fields)
        classes[contract.name] = newcls

        if (contract.name + 'Id') in types.names:
            types[contract.name + 'Id'].converter = UnwrapTypeAlias(newcls)

    return classes

