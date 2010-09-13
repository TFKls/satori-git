import sys
import getpass
from thrift.transport.TSocket import TSocket
from satori.ars.thrift import bootstrap_thrift_client
from unwrap import unwrap_interface
from token_container import token_container

#TODO: blobs

def transport_factory():
    if getpass.getuser() == 'gutowski':
        return TSocket(host='localhost', port=39889)
    if getpass.getuser() == 'zzzmwm01':
        return TSocket(host='localhost', port=37889)
    if getpass.getuser() == 'duraj':
        return TSocket(host='localhost', port=36889)
    return TSocket(host='satori.tcs.uj.edu.pl', port=38889)

print 'Bootstrapping client...'

(_interface, _client) = bootstrap_thrift_client(transport_factory)
_classes = unwrap_interface(_interface)

_module = sys.modules[__name__]
for name, value in _classes.iteritems():
    setattr(_module, name, value)

setattr(_module, '__all__', _classes.keys() + ['token_container'])

print 'Client bootstrapped.'

