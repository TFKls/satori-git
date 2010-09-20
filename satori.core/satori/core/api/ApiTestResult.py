# vim:ts=4:sts=4:sw=4:expandtab

from satori.core.cwrapper import ModelWrapper
from satori.core.models import TestResult

test_result = ModelWrapper(TestResult)

test_result._fill_module(__name__)

