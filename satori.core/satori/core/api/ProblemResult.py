# vim:ts=4:sts=4:sw=4:expandtab

from satori.core.cwrapper import ModelWrapper
from satori.core.models import ProblemResult

problem_result = ModelWrapper(ProblemResult)

problem_result._fill_module(__name__)

