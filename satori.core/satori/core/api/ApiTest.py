# vim:ts=4:sts=4:sw=4:expandtab

from satori.core.cwrapper import ModelWrapper
from satori.core.models import Test

test = ModelWrapper(Test)

test.attributes('data')

test._fill_module(__name__)

