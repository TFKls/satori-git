# vim:ts=4:sts=4:sw=4:expandtab
import unittest

from satori.ars.test_layer import DjangoTestLayer, setup_module
from django.db import models

from satori.ars import django2ars

setup_module(__name__)

class A(models.Model):
    __module__ = __name__ + '.models'

    a = models.IntegerField()
    b = models.CharField(max_length=12)

class Op(django2ars.Opers):
    y = django2ars.ModelOpers(A)

class BasicTest(unittest.TestCase):
    layer = DjangoTestLayer

    def setUp(self):
        a = A()
        a.a = 12
        a.b = "vvv"
        a.save()

    def testGetter(self):
        self.assertEqual(Op.A__a__get("", 1), 12)
        Op.A__a__set("", 1, 16)

