# vim:ts=4:sts=4:sw=4:expandtab

__all__ = (
    'Token',
)

from datetime import datetime, timedelta
import base64
import crypt
import hashlib
import random
import time
import string
from django.conf import settings
from Crypto.Cipher import AES
from satori.objects import Object, Argument
from satori.core.models import Session, Role, User, Machine
from satori.ars.model import ArsTypeAlias, ArsString

class TokenError(Exception):
    """Exception. Provided token is invalid.
    """
    pass

class ArsToken(ArsTypeAlias):
    def __init__(self):
        super(ArsToken, self).__init__(name='Token', target_type=ArsString)

    def do_needs_conversion(self):
        return True

    def do_convert_to_ars(self, value):
        return str(value)

    def do_convert_from_ars(self, value):
        return Token(value)


class Token(object):
    """
    Class for token manipulation.
    """

    @classmethod
    def ars_type(cls):
        if not hasattr(cls, '_ars_type'):
            cls._ars_type = ArsToken()

        return cls._ars_type

    @Argument('token', type=(str, None))
    @Argument('key', type=(str, None))
    @Argument('session', type=(Session, None))
    @Argument('validity', type=(timedelta, None))
    @Argument('deadline', type=(datetime, None))
    def __init__(self, token=None, key=None, session=None, validity=None, deadline=None):
        super(Token, self).__init__()
        self.key = key or settings.SECRET_KEY
        self.salt = self._salt()
        self.session = None
        self.deadline = datetime.max
        if token:
            raw = self._decrypt(token).split('\n')
            if len(raw) != 4:
                raise TokenError(
                    "TokenError: Provided token '{0}' is invalid."
                    .format(token)
                )
            self.salt = raw[0]
            self.deadline = datetime.fromtimestamp(float(raw[2]))
            if self.deadline < datetime.now():
                raise TokenError(
                    "Provided token '{0}' has expired."
                    .format(token)
                )
            if raw[1]:
                try:
                    self.session = Session.objects.get(id=raw[1])
                    if self.session.deadline < datetime.now():
                        raise TokenError(
                            "Provided token '{0}' has expired."
                            .format(token)
                        )
                except Session.DoesNotExist:
                    raise TokenError(
                        "Provided token '{0}' has expired."
                        .format(token)
                    )
            else:
                self.session = None
            if raw[3] != self._genhash():
                raise TokenError(
                    "Provided token '{0}' is malformed."
                    .format(token)
                )
        if session is not None:
            self.session = session
        if deadline is not None:
            self.deadline = deadline
        if validity is not None:
            self.deadline = datetime.now() + validity

    def _get_validity(self):
        return self.deadline - datetime.now()
    def _set_validity(self, val):
        self.deadline = datetime.now() + val
    validity = property(_get_validity, _set_validity)
    valid = property(lambda self: self.deadline > datetime.now())
    @property
    def role(self):
        if self.session is not None:
            return self.session.role
        return None
    @property
    def user(self):
        if self.session is not None:
            return self.session.user
        return None
    @property
    def machine(self):
        if self.session is not None:
            return self.session.machine
        return None
    @property
    def data(self):
        if self.session is not None:
            return self.session.data_pickle
        return None
    @property
    def session_id(self):
        if self.session is not None:
            return str(self.session.id)
        return ''

    def __str__(self):
        return self._encrypt('\n'.join([ str(x) for x in
            self.salt, self.session_id, time.mktime(self.deadline.timetuple()), self._genhash()
        ]))

    def _salt(self):
        chars = string.letters + string.digits
        salt = ''
        for i in range(8):
            salt += random.choice(chars)
        return salt

    def _hash(self, data):
        h = hashlib.md5()
        h.update(data)
        return h.hexdigest()[0:8]

    def _encode(self, data):
        return base64.urlsafe_b64encode(data)

    def _decode(self, data):
        return base64.urlsafe_b64decode(data)

    def _fillup(self, data):
        l = len(data)
        f = 'X'
        if l > 0 and data[-1] == f:
            f = 'Y'
        l = l % 16
        l = 16 - l
        ff = ''
        for i in range(l):
            ff += f
        return data + ff

    def _unfill(self, data):
        l = len(data)
        if l == 0:
            return data
        f = data[l-1]
        while data[l-1]==f:
            l = l - 1
        return data[0:l]

    def _key(self):
        h = hashlib.md5()
        h.update(self.key)
        return h.hexdigest()[:16]

    def _encrypt(self, data):
        e = AES.new(self._key())
        return self._encode(e.encrypt(self._fillup(data)))

    def _decrypt(self, data):
        e = AES.new(self._key())
        return self._unfill(e.decrypt(self._decode(data)))

    def _genhash(self):
        return self._hash('\n'.join([ str(x) for x in
            self.salt, self.session_id, time.mktime(self.deadline.timetuple())
        ]))
