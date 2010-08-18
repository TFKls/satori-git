# vim:ts=4:sts=4:sw=4:expandtab
from satori.ars.model import *
from satori.ars.naming import *
import threading

import perf

import httplib

class TokenContainer(threading.local):
    def __init__(self):
        self._token = ""

    def set_token(self, token):
        self._token = token

    def unset_token(self):
        self._token = ""

    def get_token(self):
        return self._token

token_container = TokenContainer()
blob_host = ''
blob_port = ''

def blob_con(model, id, name, group):
    if group != None:
        url = '/blob/' + str(model) + '/' + str(id) + '/' + str(group) + '/' + str(name)
    else:
        url = '/blob/' + str(model) + '/' + str(id) + '/' + str(name)
    headers = {}
    headers['Host'] = blob_host
    headers['Cookie'] = 'satori_token=' + token_container.get_token() 
    return (blob_host, blob_port, url, headers)

def blob_put(filepath, model, id, name, group=None):
    (host, port, url, headers) = blob_con(model, id, name, group)
    with open(filepath, 'r') as data:
        con = httplib.HTTPConnection(host, port)
        try:
            con.request('PUT', url, data, headers)
            res = con.getresponse()
            if res.status == 200:
                return True
            raise Exception("Server returned %d (%s) answer." % (res.status, res.reason))
        except:
            con.close()
            raise

def blob_get(filepath, model, id, name, group=None):
    (host, port, url, headers) = blob_con(model, id, name, group)
    con = httplib.HTTPConnection(host, port)
    try:
        con.request('GET', url, '', headers)
        res = con.getresponse()
        if res.status == 200:
            with open(filepath, 'w') as data:
                while True:
                    str = res.read(65536)
                    if len(str) == 0:
                        break
                    data.write(str)
                return True
        raise Exception("Server returned %d (%s) answer." % (res.status, res.reason))
    except:
        con.close()
        raise

def convert_to(elem, type):
    if elem is None:
    	return None

    if isinstance(type, ListType):
    	return [convert_to(x, type.element_type) for x in elem]

    if hasattr(type, '__realclass'):
    	return elem._id
    
    return elem

def convert_from(elem, type):
    if elem is None:
    	return None

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
        perf.begin('wrap')
#        newargs = []
	    newkwargs = {}

        if _token_type is not None:
#            newargs.append(convert_to('', _token_type))
            newkwargs['token'] = convert_to(token_container.get_token(), _token_type)

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
        ret = convert_from(ret, _rettype)
        perf.end('wrap')
        return ret

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

    def oa_get_blob(self, name, filepath):
        return blob_get(filepath, class_name, self._id, name)

    def oa_set_blob(self, name, filepath):
        return blob_put(filepath, class_name, self._id, name)

    class_dict['__init__'] = __init__
    class_dict['__getattr__'] = __getattr__
    class_dict['__setattr__'] = __setattr__
    class_dict['oa_get_blob'] = oa_get_blob
    class_dict['oa_set_blob'] = oa_set_blob

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

