# vim:ts=4:sts=4:sw=4:expandtab

__all__ = (
    'Token',
)

from datetime import datetime, timedelta
import base64
import crypt
import hashlib
import pickle
import random
import time
import urlparse
import urllib
from Crypto.Cipher import AES
from openid.consumer import consumer
from satori.objects import Object, Argument
from satori.core.settings import SECRET_KEY
from satori.sec.models import Login, OpenIdentity
from satori.sec.store import Store

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
    @Argument('data', type=(str, None), default=None)
    @Argument('validity', type=(timedelta, None), default=None)
    @Argument('deadline', type=(datetime, None), default=None)
    def __init__(self, token, key, user, auth, data, validity, deadline):
        self.key = key or SECRET_KEY
        self.data = ''
        if token is not None:
            try:
                raw = self._decrypt(token).split('\n')
                if len(raw) != 6:
                    raise TokenError(
                        "Provided token '{0}' is strange."
                        .format(token)
                    )
                self.salt = raw[0]
                self.user = raw[1]
                self.auth = raw[2]
                self.data = self._decode(raw[3])
                self.deadline = datetime.fromtimestamp(float(raw[4]))
                if raw[5] != self._genhash():
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
        if data is not None:
        	self.data = data
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
            self.salt, self.user, self.auth, self._encode(self.data), time.mktime(self.deadline.timetuple()), self._genhash()
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


class AuthenticationError(Exception):
    """Exception. Authentication failed.
    """
    pass

@Argument('login', type=str)
@Argument('password', type=str)
def authenticateByLogin(login, password):
    login = Login.objects.get(login=login)
    if crypt.crypt(password, login.password) != login.password:
        raise AuthenticationError(
            "Incorrect password."
        )
    token = Token(user=str(login.user.id), auth='login', validity=timedelta(hours=6)) 
    return str(token)


@Argument('openid', type=str)
@Argument('realm', type=str)
@Argument('return_to', type=str)
def authenticateByOpenIdStart(openid, realm, return_to):
    session = { 'id' : 'random' }
    store = Store()
    callback = urlparse.urlparse(return_to)
    qs = urlparse.parse_qs(callback.query)
    qs['__satori__openid'] = [ session['id'] ]
    query = []
    for key, vlist in qs.items():
        for value in vlist:
        	query.append((key,value))
    query = urllib.urlencode(query)
    url = urlparse.urlunparse((callback.scheme, callback.netloc, callback.path, callback.params, query, callback.fragment))
    consument = consumer.Consumer(session, store)
    request = consument.begin(openid)
    #request.addExtension
    redirect = request.redirectURL(realm, url)
    token = Token(user='', auth='openid', data=pickle.dumps(session), validity=timedelta(hours=1)) 
    return (str(token), redirect)

@Argument('token', type=str)
@Argument('args', type=dict)
@Argument('return_to', type=str)
def authenticateByOpenIdFinish(token, args, return_to):
    token = Token(token)
    if token.auth != 'openid':
        return str(token)
    session = pickle.loads(token.data)
    store = Store()
    consument = consumer.Consumer(session, store)
    response = consument.complete(args, return_to)
    if response.status != consumer.SUCCESS:
        raise AuthenticationError(
            "OpenID failed."
        )
    identity = OpenIdentity.objects.get(identity=response.identity_url)
    token = Token(user=str(identity.user.id), auth='openid', validity=timedelta(hours=6)) 
    print 'OpenIDFinish session', session
    return str(token)
