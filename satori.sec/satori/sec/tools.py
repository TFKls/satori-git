# vim:ts=4:sts=4:sw=4:expandtab

__all__ = (
    'Token',
)

from satori.objects import Object, Argument
from satori.core.settings import SECRET_KEY
from datetime import datetime, timedelta
import base64
import hashlib
import random
import time
from Crypto.Cipher import AES

class TokenError(Exception):
    """Exception. Provided token is invalid.
    """
    pass

class Token(Object):
    """
    Class for token manipulation.
    """

    @Argument('token', type=(str, None), default=None)
    @Argument('key', type=(str, None), default=None)
    @Argument('user', type=(str, None), default=None)
    @Argument('auth', type=(str, None), default=None)
    @Argument('validity', type=(timedelta, None), default=None)
    @Argument('deadline', type=(datetime, None), default=None)
    def __init__(self, token, key, user, auth, validity, deadline):
        self.key = key or SECRET_KEY
        if token is not None:
            try:
                data = self._decrypt(token).split('\n')
                if len(data) != 5:
                    raise TokenError(
                        "Provided token '{0}' is too short."
                        .format(token)
                    )
                self.salt = data[0]
                self.user = data[1]
                self.auth = data[2]
                self.deadline = datetime.fromtimestamp(float(data[3]))
                if data[4] != self._genhash():
                    raise TokenError(
                        "Provided token '{0}' is malformed."
                        .format(token)
                    )
            except TokenError:
                raise
            except:
                raise TokenError(
                    "Provided token '{0}' is invalid."
                    .format(token)
                )
        if token is None and (user is None or auth is None or (validity is None and deadline is None)):
            raise TokenError(
                "Too few arguments to create a token."
            )
        if token is None:
            self.salt = str(random.randint(100000, 999999))
        if user is not None:
            self.user = user
        if auth is not None:
            self.auth = auth
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

    def __str__(self):
        return self._encrypt('\n'.join([ str(x) for x in
            self.salt, self.user, self.auth, time.mktime(self.deadline.timetuple()), self._genhash()
        ]))

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
            self.salt, self.user, self.auth, time.mktime(self.deadline.timetuple())
        ]))

