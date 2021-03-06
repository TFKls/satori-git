# vim:ts=4:sts=4:sw=4:expandtab

from   django.db import transaction
import inspect
import sys
from   types     import NoneType

from satori.ars       import perf
from satori.ars.model import *

from satori.core.export.docstring    import trim_docstring
from satori.core.export.oa           import BadAttributeType, MissingBlob, Attribute, AnonymousAttribute, AttributeGroupField, DefaultAttributeGroupField
from satori.core.export.pc           import AccessDenied, PCDeny, PCPermit, PCArg, PCArgField, PCGlobal, PCAnd, PCOr, PCEach, PCEachKey, PCEachValue, PCTokenUser, PCRawBlob, PCTokenIsUser, PCTokenIsMachine
from satori.core.export.token        import token_container, TokenInvalid, TokenExpired
from satori.core.export.type_helpers import Binary, Struct, DefineException, TypedList, TypedMap, python_to_ars_type
from satori.core.export.types_django import ArgumentNotFound, CannotReturnObject, CannotDeleteObject, generate_django_types, ars_django_structure
from satori.core.export.types_django import DjangoId, DjangoStruct, DjangoIdList, DjangoStructList


InvalidArgument = DefineException('InvalidArgument', 'The specified argument is invalid: name={name}, reason={reason}',
    [('name', unicode, False), ('reason', unicode, False)])


exported_classes = []
global_exception_types = []


global_exception_types.append(TokenInvalid)
global_exception_types.append(TokenExpired)
global_exception_types.append(AccessDenied)
global_exception_types.append(ArgumentNotFound)
global_exception_types.append(CannotReturnObject)
global_exception_types.append(InvalidArgument)


def ExportModel(cls):
    generate_django_types(cls)

    @ExportMethod(DjangoStruct(cls), [DjangoId(cls)], PCPermit())
    def get_struct(self):
        return self

    cls.get_struct = get_struct

    @ExportMethod(DjangoStructList(cls), [DjangoStruct(cls)], PCPermit())
    @staticmethod
    def filter(arg_struct=None):
        kwargs = {}
        permissions = set()
        for (field_name, field_permission) in ars_django_structure[cls].django_fields:
            if hasattr(arg_struct, field_name) and (getattr(arg_struct, field_name) is not None):
                kwargs[field_name] = getattr(arg_struct, field_name)
                permissions.add(field_permission)

        return Privilege.wrap(cls, where=permissions).filter(**kwargs)

    cls.filter = filter

    return ExportClass(cls)


def ExportClass(cls=None, no_inherit=False):
    if cls is None:
        return lambda x: ExportClass(x, no_inherit)

    if no_inherit:
        cls._export_no_inherit = True
        
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
            transaction.enter_transaction_management()
            transaction.managed(True)

            try:
                perf.begin('token')
                token_container.check_set_token_str(kwargs.pop('token', ''))
                perf.end('token')

                perf.begin('args')
                for arg_name in kwargs:
                    kwargs[arg_name] = ars_proc.parameters[arg_name].type.convert_from_ars(kwargs[arg_name])
                perf.end('args')
                    
                if '_self' in kwargs:
                    kwargs['self'] = kwargs.pop('_self')

                if not pc(**kwargs):
                    raise AccessDenied()

                perf.begin('func')
                ret = func(**kwargs)
                perf.end('func')

                perf.begin('ret')
                ret = ars_proc.return_type.convert_to_ars(ret)
                perf.end('ret')

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
            if (arg_name == 'self'):
                arg_name = '_self'
            ars_proc.add_parameter(name=arg_name, type=python_to_ars_type(self.argument_types[i]), optional=(i >= nondef_count))

        for exception in global_exception_types:
            ars_proc.add_exception(python_to_ars_type(exception))

        for exception in self.exception_types:
            ars_proc.add_exception(python_to_ars_type(exception))

        doc = trim_docstring(self.func.__doc__)
        if doc:
            doc = doc + '\n\n'

        doc = doc + 'Required permissions: ' + str(self.pc)

        ars_proc.__doc__ = doc

        return ars_proc


def generate_service(cls, base):
    service = ArsService(name=cls.__name__, base=base)

    service.__doc__ = trim_docstring(cls.__doc__)

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
        if (parent in exported_classes) and (not cls.__dict__.get('_export_no_inherit', False)):
            base = interface.services[parent.__name__]
        else:
            base = None
        interface.add_service(generate_service(cls, base))

    return interface


def init():
    global Privilege
    from satori.core.models import Privilege

