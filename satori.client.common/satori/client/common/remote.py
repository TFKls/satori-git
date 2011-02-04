# vim:ts=4:sts=4:sw=4:expandtab

import getpass
import new
import os
import shutil
import sys
import urllib
from httplib import HTTPConnection
from StringIO import StringIO
from types import FunctionType

from thrift.transport.TSocket import TSocket

from satori.client.common import setup_api
from satori.ars.model import ArsString, ArsProcedure, ArsService, ArsInterface
from satori.ars.thrift import ThriftClient, ThriftReader
from satori.objects import Argument, Signature, ArgumentMode
from unwrap import unwrap_interface
from oa_map import get_oa_map
from token_container import token_container

client_host = ''
client_port = 0
blob_port = 0

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

def setup(host, thrift_port, blob_port_):
    global client_host, client_port, blob_port
    client_host = host
    client_port = thrift_port
    blob_port = blob_port_

    print 'Bootstrapping client...'

    (_interface, _client) = bootstrap_thrift_client(transport_factory)
    _classes = unwrap_interface(_interface, BlobReader, BlobWriter)

    _classes['token_container'] = token_container
    _classes['OaMap'] = get_oa_map(_classes['Attribute'], _classes['AnonymousAttribute'], _classes['BadAttributeType'], _classes['Blob'])

    setup_api(_classes)

    print 'Client bootstrapped.'

