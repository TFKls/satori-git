# vim:ts=4:sts=4:sw=4:expandtab
import unittest

from satori.ars.test_layer import DjangoTestLayer, setup_module
from django.db import models

from satori.ars import django_

setup_module(__name__)

class D(models.Model):
    __module__ = __name__ + '.models'

    a = models.IntegerField()
    b = models.CharField(max_length=12)

class Op(django_.Opers):
    y = django_.ModelProceduresProvider(D)

class BasicTest(unittest.TestCase):
    layer = DjangoTestLayer

    def testGetter(self):
        django_.generate_contracts()

        a = D()
        a.a = 12
        a.b = "vvv"
        a.save()

        self.assertEqual(django_.contract_list.PYTHON["D"].procedures.PYTHON["D__a__get"].implementation("", 1), 12)

        django_.contract_list.PYTHON["D"].procedures.PYTHON["D__a__set"].implementation("", 1, 16)

        self.assertEqual(django_.contract_list.PYTHON["D"].procedures.PYTHON["D__a__get"].implementation("", 1), 16)
        self.assertEqual(django_.contract_list.PYTHON["D"].procedures.PYTHON["D__b__get"].implementation("", 1), "vvv")

