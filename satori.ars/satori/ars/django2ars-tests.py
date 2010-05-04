# vim:ts=4:sts=4:sw=4:expandtab
import unittest

import satori.ars.test_setup
from django.db import models

from satori.ars import django2ars
class Z(models.Model):
    a = models.IntegerField()
    b = models.CharField(max_length=12)

class Op(django2ars.Opers):
    y = django2ars.ModelOpers(Z)

class BasicTest(unittest.TestCase):

    def setUp(self):
        satori.ars.test_setup.setupModel(Z)

        a = Z()
        a.a = 12
        a.b = "vvv"
        a.save()

    def testGetter(self):
        self.assertEqual(Op.Z__a__get("", 1), 12)
        Op.Z__a__set("", 1, 16)

