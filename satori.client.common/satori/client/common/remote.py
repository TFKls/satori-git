# vim:ts=4:sts=4:sw=4:expandtab

import sys
import os
import shutil
import getpass
import urllib
from types import FunctionType
from StringIO import StringIO
from httplib import HTTPConnection
from thrift.transport.TSocket import TSocket
from satori.ars.model import ArsString, ArsProcedure, ArsService, ArsInterface
from satori.ars.thrift import ThriftClient, ThriftReader
from satori.objects import Argument, Signature, ArgumentMode
from unwrap import unwrap_interface
from token_container import token_container

if getpass.getuser() == 'gutowski':
    client_host = 'satori.tcs.uj.edu.pl'
    client_port = 39889
    blob_port = 39887
elif (getpass.getuser() == 'zzzmwm01') or (getpass.getuser() == 'mwrobel'):
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

@Argument('transport_factory', type=FunctionType)
def bootstrap_thrift_client(transport_factory):
    interface = ArsInterface()
    idl_proc = ArsProcedure(return_type=ArsString, name='Server_getIDL')
    idl_serv = ArsService(name='Server')
    idl_serv.add_procedure(idl_proc)
    interface.add_service(idl_serv)

    bootstrap_client = ThriftClient(interface, transport_factory)
    bootstrap_client.wrap_all()
    idl = idl_proc.implementation()
    bootstrap_client.stop()

    idl_reader = ThriftReader()
    interface = idl_reader.read_from_string(idl)

    client = ThriftClient(interface, transport_factory)
    client.wrap_all()

    return (interface, client)

class BlobWriter(object):
    def __init__(self, length, model=None, id=None, name=None, group=None, filename=''):
        if model:
            url = '/blob/{0}/{1}/{2}/{3}'.format(urllib.quote(model), str(id), urllib.quote(group), urllib.quote(name))
        else:
            url = '/blob/upload'

        headers = {}
        headers['Host'] = urllib.quote(client_host)
        headers['Cookie'] = 'satori_token=' + urllib.quote(token_container.get_token())
        headers['Content-length'] = str(length)
        headers['Filename'] = urllib.quote(filename)

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
    def __init__(self, model=None, id=None, name=None, group=None, hash=None):
        if model:
            url = '/blob/{0}/{1}/{2}/{3}'.format(urllib.quote(model), str(id), urllib.quote(group), urllib.quote(name))
        else:
            url = '/blob/download/{0}'.format(urllib.quote(hash))

        headers = {}
        headers['Host'] = urllib.quote(client_host)
        headers['Cookie'] = 'satori_token=' + urllib.quote(token_container.get_token())
        headers['Content-length'] = '0'

        try:
            self.con = HTTPConnection(client_host, blob_port)
            self.con.request('GET', url, '', headers)

            self.res = self.con.getresponse()
            if self.res.status != 200:
                raise Exception("Server returned %d (%s) answer." % (self.res.status, self.res.reason))
            self.length = int(self.res.getheader('Content-length'))
            self.filename = urllib.unquote(self.res.getheader('Filename', ''))
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
def anonymous_blob_path(path):
    with open(path, 'r') as src:
        ln = os.fstat(src.fileno()).st_size
        blob = anonymous_blob(ln)
        shutil.copyfileobj(src, blob, ln)
    return blob.close()

print 'Bootstrapping client...'

(_interface, _client) = bootstrap_thrift_client(transport_factory)
_classes = unwrap_interface(_interface, BlobReader, BlobWriter)

_module = sys.modules[__name__]
for name, value in _classes.iteritems():
    setattr(_module, name, value)

setattr(_module, '__all__', _classes.keys() + ['token_container', 'anonymous_blob'])

print 'Client bootstrapped.'


