# vim:ts=4:sts=4:sw=4:expandtab

import sys
from satori.core.api import ars_interface
from unwrap import unwrap_interface
from token_container import token_container

#TODO: blobs

_classes = unwrap_interface(ars_interface.deepcopy())

_module = sys.modules[__name__]
for name, value in _classes.iteritems():
    setattr(_module, name, value)

setattr(_module, '__all__', _classes.keys() + ['token_container'])

