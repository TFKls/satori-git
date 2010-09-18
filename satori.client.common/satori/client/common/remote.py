import sys
import getpass
from httplib import HTTPConnection
from thrift.transport.TSocket import TSocket
from satori.ars.thrift import bootstrap_thrift_client
from unwrap import unwrap_interface
from token_container import token_container

#TODO: blobs

if getpass.getuser() == 'gutowski':
    client_host = 'localhost'
    client_port = 39889
    blob_port = 39887
elif getpass.getuser() == 'zzzmwm01':
    client_host = 'localhost'
    client_port = 37889
    blob_port = 37887
elif getpass.getuser() == 'duraj':
    client_host = 'localhost'
    client_port = 36889
    blob_port = 36887
else:
    client_host = 'satori.tcs.uj.edu.pl'
    client_port = 38889
    blob_port = 38887

def transport_factory():
    return TSocket(host=client_host, port=client_port)

print 'Bootstrapping client...'

class BlobWriter(object):
    def __init__(self, length, model=None, id=None, name=None, group=None):
        if group:
            url = '/blob/{0}/{1}/{2}/{3}'.format(model, str(id), group, name)
        elif model:
            url = '/blob/{0}/{1}/{2}'.format(model, str(id), name)
        else:
            url = '/blob/upload'

        headers = {}
        headers['Host'] = client_host
        headers['Cookie'] = 'satori_token=' + token_container.get_token()
        headers['Content-length'] = str(length)

        self.con = HTTPConnection(client_host, blob_port)
        try:
            self.con.request('PUT', url, '', headers)
        except:
            self.con.close()
            raise

    def write(self, data):
        try:
            ret = self.con.send(data)
        except:
            self.con.close()
            raise
        return ret

    def close(self):
        try:
            res = self.con.getresponse()
            if res.status != 200:
                raise Exception("Server returned %d (%s) answer." % (res.status, res.reason))
            length = int(res.getheader('Content-length'))
            ret = res.read(length)
        finally:
            self.con.close()
        return ret

class BlobReader(object):
    def __init__(self, model, id, name, group=None):
        if group:
            url = '/blob/{0}/{1}/{2}/{3}'.format(model, str(id), group, name)
        else:
            url = '/blob/{0}/{1}/{2}'.format(model, str(id), name)

        headers = {}
        headers['Host'] = client_host
        headers['Cookie'] = 'satori_token=' + token_container.get_token()
        headers['Content-length'] = '0'

        try:
            self.con = HTTPConnection(client_host, blob_port)
            self.con.request('GET', url, '', headers)

            self.res = self.con.getresponse()
            if self.res.status != 200:
                raise Exception("Server returned %d (%s) answer." % (self.res.status, self.res.reason))
            self.length = int(self.res.getheader('Content-length'))
        except:
            self.con.close()
            raise

    def read(self, len):
        try:
            ret = self.res.read(len)
        except:
            self.con.close()
            raise
        return ret

    def close(self):
        self.con.close()

def anonymous_blob(length):
    return BlobWriter(length)

(_interface, _client) = bootstrap_thrift_client(transport_factory)
_classes = unwrap_interface(_interface, BlobReader, BlobWriter)

_module = sys.modules[__name__]
for name, value in _classes.iteritems():
    setattr(_module, name, value)

setattr(_module, '__all__', _classes.keys() + ['token_container', 'anonymous_blob'])

print 'Client bootstrapped.'

