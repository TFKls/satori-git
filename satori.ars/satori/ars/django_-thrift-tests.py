#vim:ts=4:sts=4:sw=4:expandtab
from unittest import TestCase

from satori.objects import ReturnValue, Argument

from satori.ars.naming import Name, ClassName, MethodName, ParameterName
from satori.ars.model import Contract, Procedure, Parameter, String, Int32
from satori.ars.thrift import ThriftWriter

from satori.ars.test_layer import DjangoTestLayer, setup_module
from satori.ars import django_
from django.db import models

setup_module(__name__)

class X(models.Model):
    __model__ = __name__ + '.models'

    a = models.IntegerField()
    b = models.CharField(max_length=12)

class OpX(django_.Opers):
    x = django_.ModelProceduresProvider(X)

    @x.method
    @ReturnValue(type=str)
    @Argument(name='par1', type=int)
    @Argument(name='par2', type=str)
    def func(par1, par2):
        return par1 + '_' + par2


class Y(models.Model):
    __model__ = __name__ + '.models'

    a = models.IntegerField()
    b = models.CharField(max_length=12)

class OpY(django_.Opers):
    y = django_.ModelProceduresProvider(Y)

    y.a.set.want(False)


class StaticOp(django_.Opers):
    s = django_.StaticProceduresProvider("BadOperations")

    @s.method
    @ReturnValue(type=str)
    @Argument(name='par1', type=int)
    @Argument(name='par2', type=str)
    def do_sth_stupid(par1, par2):
        return 'false'

    @s.method
    @ReturnValue(type=str)
    @Argument(name='par1', type=int)
    @Argument(name='par2', type=str)
    def do_sth_worse(par1, par2):
        return 'nothing'


# not verifying the result, only checking if runs without throwing exceptions

class Writer(TestCase):
    layer = DjangoTestLayer

    def setUp(self):
        self.text = None

    def clear(self):
        self.text = ''

    def write(self, data):
        self.text += data

    def testTrivial(self):
        self.clear()
        django_.generate_contracts()
        writer = ThriftWriter()
        writer.contracts.update(django_.contract_list.items)
        writer.writeTo(self)
#       uncomment to check if result is correct
        print self.text
