# vim:ts=4:sts=4:sw=4:expandtab

from base64 import urlsafe_b64encode
from django.conf import settings
from django.db import models
from hashlib import sha384
import os
from tempfile import NamedTemporaryFile

from satori.dbev import Events

def blob_filename(hash):
    return os.path.join(settings.BLOB_DIR, hash[0], hash[1], hash[2], hash)

class BlobReader(object):
    def __init__(self, hash):
        self.file = open(blob_filename(hash), 'rb')
        self.length = os.fstat(self.file.fileno()).st_size

    def read(self, size=-1):
        return self.file.read(size)

    def close(self):
        self.file.close()


class BlobWriter(object):
    def __init__(self):
        dirname = os.path.join(settings.BLOB_DIR, 'temp')
        if not os.path.exists(dirname):
            os.makedirs(dirname, 0700)
        self.file = NamedTemporaryFile(dir=dirname, delete=False)
        self.hash = sha384()

    def write(self, data):
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
        return hash


class OpenAttributeManager(models.Manager):
    use_for_related_fields = True

    def oa_get(self, name):
        try:
            oa = self.get(name=name)
            return oa
        except OpenAttribute.DoesNotExist:
            return None

    def oa_get_str(self, name):
        oa = self.oa_get(name)
        if oa is None:
            return None
        elif oa.is_blob:
            raise RuntimeError('Bad attribute type: {0} is not a string attribute.'.format(name))
        else:
            return oa.value

    def oa_get_blob_hash(self, name):
        oa = self.oa_get(name)
        if oa is None:
            return None
        elif not oa.is_blob:
            raise RuntimeError('Bad attribute type: {0} is not a blob attribute.'.format(name))
        else:
            return oa.value

    def oa_open_blob(self, name):
        oa = self.oa_get(name)
        if oa is None:
            return None
        elif not oa.is_blob:
            raise RuntimeError('Bad attribute type: {0} is not a blob attribute.'.format(name))
        else:
            return BlobReader(oa.value)

    def oa_set(self, name, oa):
        (newoa, created) = self.get_or_create(name=name)
        newoa.is_blob = oa.is_blob
        newoa.value = oa.value
        if oa.is_blob and hasattr(oa, 'filename') and oa.filename is not None:
            newoa.filename = oa.filename
        else:
        	newoa.filename = ''
        newoa.save()

    def oa_set_str(self, name, value):
        self.oa_set(name, OpenAttribute(is_blob=False, value=value))

    def oa_set_blob_hash(self, name, hash, filename=''):
        self.oa_set(name, OpenAttribute(is_blob=True, value=hash, filename=filename))

    def oa_delete(self, name):
        oa = self.oa_get(name)
        if oa is not None:
            oa.delete()


class OpenAttribute(models.Model):
    """Model. Base for all kinds of open attributes.
    """
    __module__ = "satori.core.models"

    object      = models.ForeignKey('Entity', related_name='attributes')
    name        = models.CharField(max_length=50)
    is_blob     = models.BooleanField()
    value       = models.TextField()
    filename    = models.CharField(max_length=50)

    objects = OpenAttributeManager()

    def save(self, *args, **kwargs):
        if not self.is_blob:
            self.filename = ''
        super(OpenAttribute, self).save(*args, **kwargs)

    @staticmethod
    def create_blob():
        return BlobWriter()

    @staticmethod
    def open_blob(hash):
        return BlobReader(hash)

    @staticmethod
    def exists_blob(hash):
        return os.path.exists(blob_filename(hash))

    class Meta:                                                # pylint: disable-msg=C0111
        unique_together = (('object', 'name'),)

class OpenAttributeEvents(Events):
    model = OpenAttribute
    on_insert = on_update = on_delete = []
