# vim:ts=4:sts=4:sw=4:expandtab

from satori.core.cwrapper import ModelWrapper, DemandRightWrapper, OpenAttributeWrapper
from satori.core.models import Object

object = ModelWrapper(Object)

object._add_child(DemandRightWrapper(object))
object._add_child(OpenAttributeWrapper(object))

object._fill_module(__name__)

