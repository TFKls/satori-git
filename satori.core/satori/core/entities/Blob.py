# vim:ts=4:sts=4:sw=4:expandtab

import os
from base64   import urlsafe_b64encode
from hashlib  import sha384
from tempfile import NamedTemporaryFile
from types    import NoneType

from django.conf import settings
from django.db   import models

from satori.core.dbev   import Events
from satori.core.models import OpenAttribute

def blob_filename(hash):
    return os.path.join(settings.BLOB_DIR, hash[0], hash[1], hash[2], hash)

class BlobReader(object):
    def __init__(self, hash, filename='', on_close=None):
        self.file = open(blob_filename(hash), 'rb')
        self.filename = filename
        self.length = os.fstat(self.file.fileno()).st_size
        self.on_close = on_close

    def read(self, size=-1):
        return self.file.read(size)

    def close(self):
        self.file.close()
        if self.on_close:
            self.on_close()

class BlobWriter(object):
    def __init__(self, length=-1, on_close=None):
        dirname = os.path.join(settings.BLOB_DIR, 'temp')
        if not os.path.exists(dirname):
            os.makedirs(dirname, 0700)
        self.file = NamedTemporaryFile(mode='wb', dir=dirname, delete=False)
        self.hash = sha384()
        self.on_close = on_close

    def write(self, data):
        if isinstance(data, unicode):
            data = data.encode('utf-8')
        self.file.write(data)
        self.hash.update(data)

    def close(self):
        self.file.close()
        hash = urlsafe_b64encode(self.hash.digest())
        filename = blob_filename(hash)
        dirname = os.path.dirname(filename)
        if os.path.exists(filename):
            origfile = open(filename, 'rb')
            newfile = open(self.file.name, 'rb')
            origlen = os.fstat(origfile.fileno()).st_size
            newlen = os.fstat(newfile.fileno()).st_size
            if origlen != newlen:
                raise Exception('HASH COLLISION! {0} {1}'.format(filename, self.file.name))
            while origlen > 0:
                origdata = origfile.read(min(origlen, 1024))
                newdata = newfile.read(min(origlen, 1024))
                if origdata != newdata:
                    raise Exception('HASH COLLISION! {0} {1}'.format(filename, self.file.name))
                origlen -= 1024
            origfile.close()
            newfile.close()
        if not os.path.exists(dirname):
            os.makedirs(dirname, 0700)
        os.rename(self.file.name, filename)
        if self.on_close:
            self.on_close(hash)
        return hash

@ExportClass
class Blob(object):
    """
    """
    @ExportMethod(NoneType, [int, int], PCGlobal('RAW_BLOB'))
    @staticmethod
    def create(length=-1, on_close=None):
        return BlobWriter(length, on_close)

    @ExportMethod(NoneType, [unicode, unicode, int], PCGlobal('RAW_BLOB'))
    @staticmethod
    def open(hash, filename='', on_close=None):
        return BlobReader(hash, filename, on_close)

    @ExportMethod(bool, [unicode], PCGlobal('RAW_BLOB'))
    @staticmethod
    def exists(hash):
        return os.path.exists(blob_filename(hash))
