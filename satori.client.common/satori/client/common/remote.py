import sys
import getpass
from thrift.transport.TSocket import TSocket
from satori.ars.thrift import BootstrapThriftClient
from unwrap import unwrap_classes
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

_client = BootstrapThriftClient(transport_factory)
_classes = unwrap_classes(_client.wrap_all())

_module = sys.modules[__name__]
for name, value in _classes.iteritems():
    setattr(_module, name, value)

setattr(_module, '__all__', _classes.keys() + ['token_container'])

print 'Client bootstrapped.'

