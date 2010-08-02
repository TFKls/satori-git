# vim:ts=4:sts=4:sw=4:expandtab

from satori.core.cwrapper import ModelWrapper
from satori.core.models import TestSuite

test_suite = ModelWrapper(TestSuite)

test_suite._fill_module(__name__)

