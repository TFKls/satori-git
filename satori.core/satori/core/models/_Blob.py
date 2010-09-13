# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models
from satori.dbev import Events
import hashlib, base64
from StringIO import StringIO
from django.conf import settings

BLOBHASH = hashlib.sha384
HASHSIZE = (BLOBHASH().digest_size * 8 + 5) / 6

class BlobField(models.Field):
    """A django Field for BLOBs (Binary Large OBjects).

    Currently works only with postgresql_psycopg2 engine.
    """

    __metaclass__ = models.SubfieldBase

#    def db_type(self, connection):                            # pylint: disable-msg=C0103
    def db_type(self):                            # pylint: disable-msg=C0103
        """Return the database column type for this Field.
        """
        if settings.DATABASE_ENGINE == 'postgresql_psycopg2':
            return 'bytea'
        raise NotImplementedError

    def to_python(self, value):                                # pylint: disable-msg=C0103
        """Convert a value from database to Python format.
        """
        if settings.DATABASE_ENGINE == 'postgresql_psycopg2':
            if value is None:
                return value
            return str(value)
        raise NotImplementedError

    def get_db_prep_save(self, value, connection):            # pylint: disable-msg=C0103
        """Convert a value from Python to database format.
        """
        if value is None:
            return None
        if settings.DATABASE_ENGINE == 'postgresql_psycopg2':
            import psycopg2
            return psycopg2.Binary(value)
        raise NotImplementedError


class Blob(models.Model):
    """Model. BLOB, keyed by content digest.
    """
    __module__ = "satori.core.models"

    hash        = models.CharField(max_length=HASHSIZE, primary_key=True)
    data        = BlobField()

    def __init__(self, *args, **kwargs):
        super(Blob, self).__init__(*args, **kwargs)

    def open(self, mode):
        if mode == 'r':
            self._buffer = StringIO(self.data)
        elif mode == 'w':
            self._buffer = StringIO()
        else:
            raise Exception("Unsupported mode")

    def close(self):
        self.data = self._buffer.getvalue()
        self._buffer.close()

    def read(self, *args, **kwargs):
        return self._buffer.read(*args, **kwargs)

    def write(self, *args, **kwargs):
        return self._buffer.write(*args, **kwargs)

    def length(self):
        return len(self.data)

    def __setattr__(self, name, value):
        if name == 'hash':
            return
        super(Blob, self).__setattr__(name, value)
        if name == 'data':
            if self.data is None:
                self.__dict__['hash'] = None
            else:
                self.__dict__['hash'] = base64.b64encode(BLOBHASH(self.data).digest())
