import satori.core.api
from satori.ars.model import ars_deepcopy_tuple
from satori.ars.wrapper import generate_contracts
from unwrap import unwrap_classes
from token_container import token_container

#TODO: blobs

_classes = unwrap_classes(ars_deepcopy_tuple(generate_contracts()))

_module = sys.modules[__name__]
for name, value in _classes.iteritems():
    setattr(_module, name, value)

setattr(_module, '__all__', _classes.keys() + ['token_container'])

