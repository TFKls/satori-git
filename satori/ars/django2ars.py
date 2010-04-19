# vim:ts=4:sts=4:sw=4:expandtab
import new
from satori.objects import DispatchOn
from django.db import models
from satori.ars.model import Contract, Procedure, Parameter, Void, Boolean, Int32, Int64, String
from satori.ars.naming import Name, ClassName, MethodName, FieldName, AccessorName, ParameterName, NamingStyle

class OperProvider(object):
    def _addOpers(self, opers):
        pass

@DispatchOn(field=models.AutoField)
def genFieldOpers(model, field):
    field_name = field.name
    ret = []

    def read(token, id):
        obj = model.objects.get(pk=id)
        return getattr(obj, field_name)

    ret.append(FieldOper(model, field, 'read', read, Int32, (
        Parameter(name=Name(ParameterName('token')), type=String),
        Parameter(name=Name(ParameterName('id')), type=Int32))))

    return ret

@DispatchOn(field=models.IntegerField)
def genFieldOpers(model, field):
    field_name = field.name
    ret = []

    def read(token, id):
        obj = model.objects.get(pk=id)
        return getattr(obj, field_name)

    ret.append(FieldOper(model, field, 'read', read, Int32, (
        Parameter(name=Name(ParameterName('token')), type=String),
        Parameter(name=Name(ParameterName('id')), type=Int32))))

    def write(token, id, value):
        obj = model.objects.get(pk=id)
        setattr(obj, field_name, value)
        obj.save()

    ret.append(FieldOper(model, field, 'write', write, Void, (
        Parameter(name=Name(ParameterName('token')), type=String),
        Parameter(name=Name(ParameterName('id')), type=Int32),
        Parameter(name=Name(ParameterName('value')), type=Int32))))


    return ret

@DispatchOn(field=models.CharField)
def genFieldOpers(model, field):
    field_name = field.name
    ret = []

    def read(token, id):
        obj = model.objects.get(pk=id)
        return getattr(obj, field_name)

    ret.append(FieldOper(model, field, 'read', read, String, (
        Parameter(name=Name(ParameterName('token')), type=String),
        Parameter(name=Name(ParameterName('id')), type=Int32))))

    def write(token, id, value):
        obj = model.objects.get(pk=id)
        setattr(obj, field_name, value)
        obj.save()

    ret.append(FieldOper(model, field, 'write', write, Void, (
        Parameter(name=Name(ParameterName('token')), type=String),
        Parameter(name=Name(ParameterName('id')), type=Int32),
        Parameter(name=Name(ParameterName('value')), type=String))))


    return ret

class FieldOper(object):
    def __init__(self, model, field, name, implement, return_type, parameters):
        self._model = model
        self._field = field
        self._name = name

        self._ars_name = Name(ClassName(model._meta.object_name), FieldName(field.name), AccessorName(name))
        self._ars_parameters = parameters
        self._ars_return_type = return_type

        self._want = True
        self._can = None
        self._implement = implement

    def can(self, proc):
        self._can = proc
        return proc

    def want(self, value):
        self._want = value

    def implement(self, proc):
        self._implement = proc
        return proc

    def _addOpers(self, opers):
        if not self._want:
            return

        can = self._can
        implement = self._implement

        if can:
            def func(*args, **kwargs):
                can(*args, **kwargs)
                return implement(*args, **kwargs)
        else:
            def func(*args, **kwargs):
                return implement(*args, **kwargs)

        func.__name__ = NamingStyle.IDENTIFIER.format(self._ars_name)
        func.func_name = func.__name__

        proc = Procedure(name=self._ars_name, return_type=self._ars_return_type, implementation=func)
        for param in self._ars_parameters:
            proc.addParameter(param)

        opers.append(proc)

class FieldOpers(object):
    def __init__(self, model, field):
        self._model = model
        self._field = field

        self._opers = genFieldOpers(model, field)

        for oper in self._opers:
            setattr(self, oper._name, oper)

    def _addOpers(self, opers):
        for oper in self._opers:
            oper._addOpers(opers)

class ModelOpers(OperProvider):
    def __init__(self, model):
        self.model = model
        self._field_operss = []
        for field in self.model._meta.fields:
            field_opers = FieldOpers(model, field)
            self._field_operss.append(field_opers)
            setattr(self, field.name, field_opers)

    def _addOpers(self, opers):
        for field_opers in self._field_operss:
            field_opers._addOpers(opers)

contract = Contract(name=Name(ClassName('DjangoContract')))

class OpersBase(type):
    def __new__(cls, name, bases, dct):
        opers = []

        for elem in dct.itervalues():
            if isinstance(elem, OperProvider):
                elem._addOpers(opers)

        newdct = {}

        for oper in opers:
            newdct[NamingStyle.IDENTIFIER.format(oper.name)] = staticmethod(oper.implementation)
            contract.addProcedure(oper)

        return super(OpersBase, cls).__new__(cls, name, bases, newdct)

    def __init__(cls, name, bases, dct):
        super(OpersBase, cls).__init__(name, bases, dct)

class Opers(object):
    __metaclass__ = OpersBase

