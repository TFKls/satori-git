# vim:ts=4:sts=4:sw=4:expandtab

from satori.core.cwrapper import ModelWrapper
from satori.core.models import ProblemMapping

problem_mapping = ModelWrapper(ProblemMapping)

problem_mapping._fill_module(__name__)

