import os
import shutil
from satori.ars.model import ArsTypeAlias, ArsInt64, ArsStructure
from satori.ars.wrapper import ArsDateTime, ArsNullableStructure
from satori.ars import perf
from token_container import token_container

class ArsUnwrapClass(ArsTypeAlias):
    def __init__(self, cls):
        super(ArsUnwrapClass, self).__init__(name=cls.__name__, target_type=ArsInt64)
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


def unwrap_procedure(_proc):
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

def unwrap_service(service, base, fields, BlobReader, BlobWriter):
    class_name = service.name
    class_dict = {}

    for proc in service.procedures:
        meth_name = proc.name.split('_', 1)[1]
        if meth_name.endswith('_get_blob'):
            group_name = meth_name[:-9]
            if group_name == 'oa':
            	group_name = None
            def blob_get(self, name):
                return BlobReader(class_name, self.id, name, group_name)
            class_dict[meth_name] = blob_get
            def blob_get_path(self, name, path):
                with open(path, 'w') as dst:
                    blob = blob_get(self, name)
                    shutil.copyfileobj(blob, dst, blob.length)
                return blob.close()
            class_dict[meth_name+'_path'] = blob_get_path
        elif meth_name.endswith('_set_blob'):
            group_name = meth_name[:-9]
            if group_name == 'oa':
            	group_name = None
            def blob_set(self, name, length):
                return BlobWriter(length, class_name, self.id, name, group_name)
            class_dict[meth_name] = blob_set
            def blob_set_path(self, name, path):
                with open(path, 'r') as src:
                    ln = os.fstat(src.fileno()).st_size
                    blob = blob_set(self, name, ln)
                    shutil.copyfileobj(src, blob, ln)
                return blob.close()
            class_dict[meth_name+'_path'] = blob_set_path
        else:
            class_dict[meth_name] = unwrap_procedure(proc)

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


def unwrap_interface(interface, BlobReader, BlobWriter):
    for type in interface.types:
        if type.name == 'DateTime':
            type.converter = ArsDateTime()
        elif isinstance(type, ArsStructure):
            if type.fields and (type.fields[0].name == 'null_fields'):
                newtype = ArsNullableStructure(name=type.name)
                for field in type.fields:
                    if field.name != 'null_fields':
                        newtype.add_field(field)
                type.converter = newtype

    classes = {}
    for service in interface.services:
        if service.base:
            base = classes[service.base.name]
        else:
            base = UnwrapBase

        if service.name + 'Struct' in interface.types:
            struct = interface.types[service.name + 'Struct']
            if isinstance(struct.converter, ArsNullableStructure):
                fields = [field.name for field in struct.fields][1:]
            else:
                fields = [field.name for field in struct.fields]
        else:
            fields = None
            
        newcls = unwrap_service(service, base, fields, BlobReader, BlobWriter)
        classes[service.name] = newcls

        if (service.name + 'Id') in interface.types:
            interface.types[service.name + 'Id'].converter = ArsUnwrapClass(newcls)
    
    for constant in interface.constants:
    	classes[constant.name] = constant.type.convert_from_ars(constant.value)

    return classes

