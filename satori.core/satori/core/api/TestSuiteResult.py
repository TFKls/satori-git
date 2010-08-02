# vim:ts=4:sts=4:sw=4:expandtab

from satori.core.cwrapper import ModelWrapper
from satori.core.models import TestSuiteResult

test_suite_result = ModelWrapper(TestSuiteResult)

test_suite_result._fill_module(__name__)

