# vim:ts=4:sts=4:sw=4:expandtab
import unittest

import satori.ars.test_setup
from django.db import models

from satori.ars import django2ars

class X(models.Model):
    a = models.IntegerField()
    b = models.CharField(max_length=12)

class Op(django2ars.Opers):
    y = django2ars.ModelOpers(X)

class BasicTest(unittest.TestCase):

    def setUp(self):
        satori.ars.test_setup.setupModel(X)

        a = X()
        a.a = 12
        a.b = "vvv"
        a.save()

    def testGetter(self):
        self.assertEqual(Op.X_a_read("", 1), 12)

