# vim:ts=4:sts=4:sw=4:expandtab

from   datetime  import datetime
import inspect
from   time      import mktime
import threading
from   types     import NoneType
import sys

from satori.ars       import perf
from satori.ars.model import *

exported_classes = []
global_exception_types = []


class TypedList(object):
    def __init__(self, element_type):
        self.element_type = element_type
    
    def ars_type(self):
        if not hasattr(self, '_ars_type'):
            self._ars_type = ArsList(python_to_ars_type(self.element_type))

        return self._ars_type


class TypedMap(object):
    def __init__(self, key_type, value_type):
        self.key_type = key_type
        self.value_type = value_type
    
    def ars_type(self):
        if not hasattr(self, '_ars_type'):
            ars_key_type = python_to_ars_type(self.key_type)
            ars_value_type = python_to_ars_type(self.value_type)
            self._ars_type = ArsMap(key_type=ars_key_type, value_type=ars_value_type)

        return self._ars_type


def Struct(name, fields):
    ars_type = ArsStructure(name=name)
    for (field_name, field_type, field_optional) in fields:
        ars_type.add_field(name=field_name, type=python_to_ars_type(field_type), optional=field_optional)
    return ars_type.get_class()


def DefineException(name, message, fields=[]):
    ars_exception = ArsException(name=name)
    ars_exception.add_field(name='message', type=ArsString, optional=False)
    for (field_name, field_type, field_optional) in fields:
        ars_exception.add_field(name=field_name, type=python_to_ars_type(field_type), optional=field_optional)

    exception_class = ars_exception.get_class()

    def __init__(self, **kwargs):
        kwargs['message'] = message.format(**kwargs)
        super(exception_subclass, self).__init__(**kwargs)

    exception_subclass = type(name, (exception_class,), {'__init__': __init__})

    return exception_subclass


class ArsDateTime(ArsTypeAlias):
    def __init__(self, ):
        super(ArsDateTime, self).__init__(name='DateTime', target_type=ArsInt64)

    def do_needs_conversion(self):
        return True

    def do_convert_to_ars(self, value):
        return long(mktime(value.timetuple()))

    def do_convert_from_ars(self, value):
        return datetime.fromtimestamp(value)


TokenInvalid = DefineException('TokenInvalid', 'The provided token is invalid')
TokenExpired = DefineException('TokenExpired', 'The provided token has expired')
AccessDenied = DefineException('AccessDenied', 'You don\'t have rights to call this procedure')

global_exception_types.append(TokenInvalid)
global_exception_types.append(TokenExpired)
global_exception_types.append(AccessDenied)


class TokenContainer(threading.local):
    def __init__(self):
        self.token = None

token_container = TokenContainer()


class PCPermit(object):
    def __call__(__pc__self, **kwargs):
        return True

class PCArg(object):
    def __init__(__pc__self, name, perm):
        super(PCArg, __pc__self).__init__()
        __pc__self.name = name
        __pc__self.perm = perm

    def __call__(__pc__self, **kwargs):
        return Privilege.demand(kwargs[__pc__self.name], __pc__self.perm)


class PCGlobal(object):
    def __init__(__pc__self, perm):
        super(PCGlobal, __pc__self).__init__()
        __pc__self.perm = perm

    def __call__(__pc__self, **kwargs):
        return Privilege.global_demand(__pc__self.perm)


class PCAnd(object):
    def __init__(__pc__self, *subs):
        super(PCAnd, __pc__self).__init__()
        __pc__self.subs = subs

    def __call__(__pc__self, **kwargs):
        return all(x(**kwargs) for x in __pc__self.subs)


class PCOr(object):
    def __init__(__pc__self, *subs):
        super(PCOr, __pc__self).__init__()
        __pc__self.subs = subs

    def __call__(__pc__self, **kwargs):
        return any(x(**kwargs) for x in __pc__self.subs)


class PCEach(object):
    def __init__(__pc__self, name, sub):
        super(PCEach, __pc__self).__init__()
        __pc__self.name = name
        __pc__self.sub = sub

    def __call__(__pc__self, **kwargs):
        return all(__pc__self.sub(item=x) for x in kwargs[__pc__self.name])


class PCEachKey(object):
    def __init__(__pc__self, name, sub):
        super(PCEachKey, __pc__self).__init__()
        __pc__self.name = name
        __pc__self.sub = sub

    def __call__(__pc__self, **kwargs):
        return all(__pc__self.sub(item=x) for x in kwargs[__pc__self.name].keys())


class PCEachValue(object):
    def __init__(__pc__self, name, sub):
        super(PCEachValue, __pc__self).__init__()
        __pc__self.name = name
        __pc__self.sub = sub

    def __call__(__pc__self, **kwargs):
        return all(__pc__self.sub(item=x) for x in kwargs[__pc__self.name].values())


class PCTokenUser(object):
    def __init__(__pc__self, name):
        super(PCTokenUser, __pc__self).__init__()
        __pc__self.name = name

    def __call__(__pc__self, **kwargs):
        return token_container.token.user_id == kwargs[__pc__self.name].id


python_basic_types = {
    NoneType: ArsVoid,
    int: ArsInt32,
    long: ArsInt64,
    str: ArsString,
    unicode: ArsString,
    basestring: ArsString,
    bool: ArsBoolean,
    datetime: ArsDateTime(),
}

def python_to_ars_type(type_):
    if type_ in python_basic_types:
        return python_basic_types[type_]

    if hasattr(type_, 'ars_type'):
        return type_.ars_type()

    raise RuntimeError('Cannot convert type {0} to ars type.'.format(type_))


def ExportClass(cls):
    exported_classes.append(cls)
    return cls


class ExportMethod(object):
    def __init__(self, return_type, argument_types, pc, throws=[]):
        self.return_type = return_type
        self.argument_types = argument_types
        self.exception_types = throws
        self.pc = pc

    def __call__(self, func):
        if func.__class__ == staticmethod(0).__class__:
            real_func = func.__get__(0, 0)
        else:
            real_func = func
            
        if len(inspect.getargspec(real_func)[0]) != len(self.argument_types):
            raise RuntimeError('Bad argument count in export declaration for {0}()'.format(real_func.__name__))

        real_func._export_method = self
        self.func = real_func
        return func

    def generate_procedure(self, class_name):
        func = self.func
        pc = self.pc

        def reimplementation(**kwargs):
            from   django.db import connection, transaction
            transaction.enter_transaction_management()
            transaction.managed(True)

            try:
                try:
                    token_container.token = Token(kwargs.pop('token', ''))
                except:
                    raise TokenInvalid()

                if not token_container.token.valid:
                    raise TokenExpired()

                if token_container.token.user_id:
                    userid = int(token_container.token.user_id)
                else:
                    userid = -2

                cursor = connection.cursor()
                cursor.callproc('set_user_id', [userid])
                cursor.close()

                
                for arg_name in kwargs:
                    kwargs[arg_name] = ars_proc.parameters[arg_name].type.convert_from_ars(kwargs[arg_name])

                if not pc(**kwargs):
                    raise AccessDenied()

                perf.begin('func')
                ret = func(**kwargs)
                perf.end('func')

                ret = ars_proc.return_type.convert_to_ars(ret)

                transaction.commit()
                transaction.leave_transaction_management()
            except Exception as exception:
                if isinstance(exception, ArsExceptionBase):
                    exception = exception.ars_type().convert_to_ars(exception)

                transaction.rollback()
                transaction.leave_transaction_management()

                raise exception, None, sys.exc_info()[2]
            else:
                return ret


        (args, varargs, varkw, defaults) = inspect.getargspec(self.func)

        if defaults is None:
            nondef_count = len(args)
        else:
            nondef_count = len(args) - len(defaults)

        ars_proc = ArsProcedure(name=(class_name + '_' + self.func.__name__), implementation=reimplementation, return_type=python_to_ars_type(self.return_type))

        ars_proc.add_parameter(name='token', type=ArsString, optional=False)

        for (i, arg_name) in enumerate(args):
            ars_proc.add_parameter(name=arg_name, type=python_to_ars_type(self.argument_types[i]), optional=(i >= nondef_count))

        for exception in global_exception_types:
            ars_proc.add_exception(python_to_ars_type(exception))

        for exception in self.exception_types:
            ars_proc.add_exception(python_to_ars_type(exception))

        return ars_proc


def generate_service(cls, base):
    service = ArsService(name=cls.__name__, base=base)

    for (name, function) in sorted(cls.__dict__.items()):
        if function.__class__ == staticmethod(0).__class__:
            function = function.__get__(0, 0)

        if hasattr(function, '_export_method'):
            service.add_procedure(function._export_method.generate_procedure(cls.__name__))

    return service


def generate_interface():
    interface = ArsInterface()

    for cls in exported_classes:
        parent = inspect.getmro(cls)[1]
        if parent in exported_classes:
            base = interface.services[parent.__name__]
        else:
            base = None
        interface.add_service(generate_service(cls, base))

    return interface


