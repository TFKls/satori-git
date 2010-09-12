import sys
import satori.core.api
from satori.ars.wrapper import generate_interface
from unwrap import unwrap_interface
from token_container import token_container

#TODO: blobs

_classes = unwrap_interface(generate_interface().deepcopy())

_module = sys.modules[__name__]
for name, value in _classes.iteritems():
    setattr(_module, name, value)

setattr(_module, '__all__', _classes.keys() + ['token_container'])

