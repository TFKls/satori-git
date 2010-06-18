# vim:ts=4:sts=4:sw=4:expandtab
from satori.ars.model import *
from satori.ars.naming import *
import new

id_types = {}
array_types = {}
classes = {}

def convert_to(elem, type):
    if type in id_types:
    	return elem._id
    
    return elem

def convert_from(elem, type):
    if type in id_types:
    	return id_types[type](elem)

    return elem

class ArsMethod(object):
    def __init__(self, proc):
        self._proc = proc.implementation
        self._rettype = proc.return_type
        self._argnames = map(lambda x: NamingStyle.PYTHON.format(x.name), proc.parameters.items)
        self._argtypes = map(lambda x: x.type, proc.parameters.items)
        self._procname = NamingStyle.PYTHON.format(proc.name)

        if self._argnames and (self._argnames[0] == 'token'):
        	self._argnames.pop(0)
        	self._type_token = self._argtypes.pop(0)
        	self._want_token = True
        else:
        	self._want_token = False

        if self._argnames and (self._argnames[0] == 'self'):
        	self._argnames.pop(0)
        	self._type_self = self._argtypes.pop(0)
        	self._want_self = True
        else:
        	self._want_self = False        

    def __get__(self, cls_self, cls):
        def func(*args):
            newargs = []

            if self._want_token:
            	newargs.append(convert_to('', self._type_token))

            if self._want_self:
            	newargs.append(convert_to(cls_self, self._type_self))

            if len(args) != len(self._argtypes):
                raise TypeError('{0} takes exactly {1} arguments ({2} given)'.format(self._procname, len(self._argtypes), len(args)))

            for (arg, argtype) in zip(args, self._argtypes):
            	newargs.append(convert_to(arg, argtype))

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
        if hasattr(self, name + '__get'):
        	return self.getattr(name + '__get')()
        else:
        	return AttributeError("'{0}' object has no attribute '{1}'".format(class_name, name))

    def __setattr__(self, name):
        if hasattr(self, name + '__set'):
        	return self.getattr(name + '__set')()
        else:
        	return AttributeError("'{0}' object has no attribute '{1}'".format(class_name, name))

    class_dict['__init__'] = __init__

    return new.classobj(class_name, class_bases, class_dict)

def process(reader):
    for contract in reader.contracts:
        c_name = NamingStyle.PYTHON.format(contract.name)

        newcls = generate_class(contract)

        id_name = NamingStyle.IDENTIFIER.format(Name(ClassName(c_name + 'Id')))
        if id_name in reader.types:
        	id_types[reader.types[id_name]] = newcls

        array_name = NamingStyle.IDENTIFIER.format(Name(ClassName(c_name + 'IdArray')))
        if array_name in reader.types:
        	array_types[reader.types[array_name]] = newcls

        classes[c_name] = newcls

