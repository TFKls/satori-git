# vim:ts=4:sts=4:sw=4:expandtab
from satori.ars.model import *
from satori.ars.naming import *

def convert_to(elem, type):
    if isinstance(type, ListType):
    	return [convert_to(x, type.element_type) for x in elem]

    if hasattr(type, '__realclass'):
    	return elem._id
    
    return elem

def convert_from(elem, type):
    if isinstance(type, ListType):
    	return [convert_from(x, type.element_type) for x in elem]

    if hasattr(type, '__realclass'):
    	return type.__realclass(elem)

    return elem

def wrap(_client, _proc, _procname):
    _implementation = _proc.implementation
    _rettype = _proc.return_type
    _args = [(NamingStyle.PYTHON.format(param.name), param.type, param.optional) for param in _proc.parameters.items]

    _token_type = None
    if _args and (_args[0][0] == 'token'):
        _token_type = _args.pop(0)[1]

    def func(*args, **kwargs):
#        newargs = []
	    newkwargs = {}

        if _token_type is not None:
#            newargs.append(convert_to('', _token_type))
            newkwargs['token'] = convert_to('', _token_type)

        if len(args) > len(_args):
            raise TypeError('{0}() takes at most {1} arguments ({2} given)'.format(_procname, len(_args), len(args)))

        for i in range(len(_args)):
        	(argname, argtype, argoptional) = _args[i]
            if i < len(args):
#                newargs.append(convert_to(args[i], argtype))
                newkwargs[argname] = convert_to(args[i], argtype)
                if argname in kwargs:
                    raise TypeError('{0}() got multiple values for keyword argument \'{1}\''.format(_procname, argname))
            elif argname in kwargs:
#                newargs.append(convert_to(kwargs.pop(argname), argtype))
                newkwargs[argname] = convert_to(kwargs.pop(argname), argtype)
            elif argoptional:
#                newargs.append(None)
                newkwargs[argname] = None
            else:
                raise TypeError('{0}() didn\'t get required argument \'{1}\''.format(_procname, argname))

        for argname in kwargs:
            raise TypeError('{0} got an unexpected keyword argument \'{1}\''.format(_procname, argname))

#        ret = _implementation(*newargs)
        ret = _client.call(_proc, newkwargs)

        return convert_from(ret, _rettype)

    func.func_name = _procname

    if not (_args and (_args[0][0] == 'self')):
    	func = staticmethod(func)

    return func

def generate_class(client, contract):
    class_name = NamingStyle.PYTHON.format(contract.name)
    class_bases = (object, )
    class_dict = {}

    for proc in contract.procedures:
        meth_name = NamingStyle.PYTHON.format(Name(*proc.name.components[1:]))
        class_dict[meth_name] = wrap(client, proc, meth_name)

    def __init__(self, id):
        self._id = id

    def __getattr__(self, name):
        if name == 'id':
        	return self._id
        if (name[-5:] == '__get') or (name[-5:] == '__set'):
        	raise AttributeError('\'{0}\' object has no attribute \'{1}\''.format(class_name, name))
        if hasattr(self, name + '__get'):
        	return getattr(self, name + '__get')()
        else:
        	raise AttributeError('\'{0}\' object has no attribute \'{1}\''.format(class_name, name))
        
    def __setattr__(self, name, value):
        if name[-5:] == '__set':
        	return super(self.__class__, self).__setattr__(name, value)
        if hasattr(self, name + '__set'):
        	return getattr(self, name + '__set')(value)
        else:
        	return super(self.__class__, self).__setattr__(name, value)

    class_dict['__init__'] = __init__
    class_dict['__getattr__'] = __getattr__
    class_dict['__setattr__'] = __setattr__

    return type(class_name, class_bases, class_dict)

def generate_classes(client):
    classes = {}
    types = NamedTuple()
    for contract in client.contracts:
    	types.extend(namedTypes(contract))
    for contract in client.contracts:
        c_name = NamingStyle.PYTHON.format(contract.name)

        newcls = generate_class(client, contract)

        id_name = NamingStyle.IDENTIFIER.format(Name(ClassName(c_name + 'Id')))
        if id_name in types.IDENTIFIER:
        	types.IDENTIFIER[id_name].__realclass = newcls

        classes[c_name] = newcls
    return classes

