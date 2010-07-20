# vim:ts=4:sts=4:sw=4:expandtab
from satori.ars.model import *
from satori.ars.naming import *
import new

id_types = {}

def convert_to(elem, type):
    if isinstance(type, ListType):
    	return [convert_to(x, type.element_type) for x in elem]

    if hasattr(type, __realclass):
    	return elem._id
    
    return elem

def convert_from(elem, type):
    if isinstance(type, ListType):
    	return [convert_from(x, type.element_type) for x in elem]

    if hasattr(type, __realclass):
    	return type.__realclass(elem)

    return elem

class ArsMethod(object):
    def __init__(self, proc):
        self._proc = proc.implementation
        self._rettype = proc.return_type
        self._argnames = []
        self._argtype = {}
        self._argoptional = {}
        self._procname = NamingStyle.PYTHON.format(proc.name)
        for param in proc.parameters.items:
        	argname = NamingStyle.PYTHON.format(param.name)
        	self._argnames.append(argname)
        	self._argtype[argname] = param.type
        	self._argoptional[argname] = param.optional

        if self._argnames and (self._argnames[0] == 'token'):
        	self._argnames.pop(0)
        	self._want_token = True
        else:
        	self._want_token = False

        if self._argnames and (self._argnames[0] == 'self'):
        	self._argnames.pop(0)
        	self._want_self = True
        else:
        	self._want_self = False        

    def __get__(self, cls_self, cls):
        def func(*args, **kwargs):
            usedargs = set()

            newargs = []

            if self._want_token:
            	newargs.append(convert_to('', self._argtype['token']))
            	usedargs.add('token')

            if self._want_self:
            	newargs.append(convert_to(cls_self, self._argtype['self']))
            	usedargs.add('self')

            if len(args) > len(self._argnames):
                raise TypeError('{0} takes at most {1} arguments ({2} given)'.format(self._procname, len(self._argnames), len(args)))

            for i in range(len(self._argnames)):
            	argname = self._argnames[i]
                if i < len(args):
            	    newargs.append(convert_to(args[i], self._argtype[argname]))
                    if argname in kwargs:
                        raise TypeError('{0} got an unexpected keyword argument \'{1}\''.format(self._procname, argname))
                elif argname in kwargs:
                    newargs.append(convert_to(kwargs[argname], self._argtype[argname]))
                elif self._argoptional[argname]:
                    newargs.append(None)
                else:
                    raise TypeError('{0} didn\'t get required argument \'{1}\''.format(self._procname, argname))

            for argname in kwargs:
                if not argname in self._argtype:
                    raise TypeError('{0} got an unexpected keyword argument \'{1}\''.format(self._procname, argname))
            
            ret = self._proc(*newargs)

            return convert_from(ret, self._rettype)

        func.func_name = self._procname
        return func

    def __str__():
        return 'ArsMethod:{0}'.format(self._procname)

def generate_class(contract):
    class_name = NamingStyle.PYTHON.format(contract.name)
    class_bases = (object, )
    class_dict = {}

    for proc in contract.procedures:
        meth_name = NamingStyle.PYTHON.format(Name(*proc.name.components[1:]))
        meth = ArsMethod(proc)

        class_dict[meth_name] = meth

    def __init__(self, id):
        self._id = id

    def __getattr__(self, name):
        if (name[-5:] == '__get') or (name[-5:] == '__set'):
        	raise AttributeException("AA")
        if hasattr(self, name + '__get'):
        	return getattr(self, name + '__get')()
        else:
        	raise AttributeException("AA")

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

    return new.classobj(class_name, class_bases, class_dict)

def process(contracts):
    classes = {}
    types = NamedTuple()
    for contract in contracts:
    	types.extend(namedTypes(contract))
    for contract in contracts:
        c_name = NamingStyle.PYTHON.format(contract.name)

        newcls = generate_class(contract)

        id_name = NamingStyle.IDENTIFIER.format(Name(ClassName(c_name + 'Id')))
        if id_name in types.IDENTIFIER:
        	types.IDENTIFIER[id_name].__realclass = newcls

        classes[c_name] = newcls
    return classes

