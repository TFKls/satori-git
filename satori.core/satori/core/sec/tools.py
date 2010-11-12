# vim:ts=4:sts=4:sw=4:expandtab

__all__ = (
    'Token',
    'RoleSet',
    'RightCheck',
)

from datetime import datetime, timedelta
import base64
import crypt
import hashlib
import random
import time
import string
import urlparse
import urllib
import traceback
from satori.ars import perf
from django.core import cache
from django.conf import settings
from django.db import models
from Crypto.Cipher import AES
from satori.objects import Object, Argument
from satori.core.sec.store import Store
from satori.core.models import Session, Role, User, Privilege, Global, Entity
from satori.ars.model import ArsTypeAlias, ArsString
from psycopg2._psycopg import adapt
from django.db import connection

class permarg_list_adapter(object):
 def __init__(self, c):
   self.c = c
 def prepare(self, conn):
   self.a = adapt(self.c)
   self.a.prepare(conn)
 def getquoted(self):
   res = self.a.getquoted() + '::permarg[]'
   return res

class permarg_list(object):
 def __init__(self, c):
   self.c = c
 def __conform__(self, proto):
   return permarg_list_adapter(self.c)


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
    @Argument('user', type=(Role, None))
    @Argument('user_id', type=(str, None))
    @Argument('auth', type=(str, None))
    @Argument('data')
    @Argument('validity', type=(timedelta, None))
    @Argument('deadline', type=(datetime, None))
    def __init__(self, token=None, key=None, user=None, user_id=None, auth=None, data=None, validity=None, deadline=None):
        super(Token, self).__init__()
        self.key = key or settings.SECRET_KEY
        self.data_id = ''
        if token is not None:
            if token == '':
                self.salt = self._salt()
                self.user_id = ''
                self.auth = ''
                self.data_id = ''
                self.deadline = datetime.max
            else:
                try:
                    raw = self._decrypt(token).split('\n')
                    if len(raw) != 6:
                        raise TokenError(
                            "Provided token '{0}' is strange."
                            .format(token)
                        )
                    self.salt = raw[0]
                    self.user_id = raw[1]
                    self.auth = raw[2]
                    self.data_id = raw[3]
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
                        "TokenError: Provided token '{0}' is invalid."
                        .format(token)
                    )
        if user is not None and user_id is None:
            user_id = str(user.id)
        if token is None and (user_id is None or auth is None or (validity is None and deadline is None)):
            raise TokenError(
                "Too few arguments to create a token."
            )
        if token is None:
            self.salt = self._salt()
        if user_id is not None:
            self.user_id = user_id
        if auth is not None:
            self.auth = auth
        if data is not None:
        	self._set_data(data)
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
    def user(self):
        try:
            return Role.objects.get(id=self.user_id)
        except:
            pass
        return None

    def _get_data(self):
        try:
            return Session.objects.get(id=self.data_id).data_pickle
        except:
            traceback.print_exc()
            pass
        return None
    def _set_data(self, data):
        if data is None:
            if self.data_id != '':
                Session.objects.filter(id=self.data_id).delete()
                self.data_id = ''
        else:
            try:
                ses = Session.objects.get(id=self.data_id)
            except:
                ses = Session()
            ses.data_pickle = data
            ses.save()
            self.data_id = ses.id
    data = property(_get_data, _set_data)


    def __str__(self):
        return self._encrypt('\n'.join([ str(x) for x in
            self.salt, self.user_id, self.auth, self.data_id, time.mktime(self.deadline.timetuple()), self._genhash()
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
            self.salt, self.user_id, self.auth, self.data_id, time.mktime(self.deadline.timetuple())
        ]))


class RoleSetError(Exception):
    """Exception. Roles structure is corrupted.
    """
    pass

class RoleSet(object):
    def _dfs(self, role):
        if role not in self._absorb:
            abs = None
            for parent in role.parents.all():
                a = self._dfs(parent)
                if a is not None:
                    if abs is not None and abs != a:
                        raise RoleSetError(
                            "Multiple absorbing roles."
                        )
                    abs = a
            self._absorb[role] = abs
        return self._absorb[role]

    @Argument('token', type=Token)
    def __init__(self, token):
        super(RoleSet, self).__init__()
        self._ts = datetime.now()
        self._absorb = dict()
        globe = Global.get_instance()
        roles = set()
        roles.add(globe.anonymous)
        if token.user != None and token.valid:
            roles.add(globe.authenticated)
            try:
                abs = self._dfs(token.user)

                if abs:
                    roles.clear()
                    self._absorb = dict()
                    self._dfs(abs)
                for (role,a) in self._absorb.items():
                    roles.add(role)
            except:
                pass
        self.roles = frozenset(roles)

class RightCheck(object):
    cache = {}

    def __init__(self):
        super(RightCheck, self).__init__()
        self._ts = datetime.now()
        self._cache_hit = 0
        self._cache_miss = 0
        self._cache_time = 0
        self._cache_add = 0
        pass

    def _cache_key(self, role, object, right):
        return str(role.id)+'_'+str(object.id)+'_'+str(right)
    def _cache_set(self, role, object, right, value):
        key = self._cache_key(role, object, right)
        self._cache_add += 1
        if value:
            RightCheck.cache[key] = (True, self._ts + timedelta(seconds=120))
        else:
        	RightCheck.cache[key] = (False, self._ts + timedelta(seconds=30))

    def _cache_get(self, role, object, right):
        key = self._cache_key(role, object, right)
        val = RightCheck.cache.get(key, None)
        if val is None:
            self._cache_miss += 1
        	return val
        if val[1] < self._ts:
            del RightCheck.cache[key]
            self._cache_time += 1
        	return None;
        self._cache_hit += 1
        return val[0]

    def _upgrade_model(self, object):
        model = models.get_model(*object.model.split('.'))
        if not isinstance(object, model):
            object = model.objects.get(id=object.id)
        return object

    def _inherit_all(self, object, right):
        perf.begin('inherit')
        object = self._upgrade_model(object)
        all = { object.id: { right: [] } }
        ret = [(object, right)]
        i = 0
        while i < len(ret):
        	object, right = ret[i]
        	i = i + 1
            for (obj, rig) in object.inherit_right(right):
                if obj.id not in all:
                	all[obj.id] = {}
                if rig not in all[obj.id]:
                	all[obj.id][rig] = []
                    obj = self._upgrade_model(obj)
                	ret.append((obj, rig))
                all[obj.id][rig].append((object, right))
        ret.reverse()
        perf.end('inherit')
        return ret,all

    def _single_check(self, role, object, right):
        res = self._cache_get(role, object, right)
        if res is not None:
            return res
        res = False
        for priv in Privilege.objects.filter(role = role, entity = object, right = right):
            if priv.start_on is not None and priv.start_on > self._ts or priv.finish_on is not None and priv.finish_on < self._ts:
                continue
            res = True
            break
        return res

    def _rec_cache_true(self, role, object, right, all, start =True):
        if start:
        	self._vis = set()
        if (object.id, right) in self._vis:
        	return
        self._vis.add((object.id, right))
        self._cache_set(role, object, right, True)
        for obj, rig in all[object.id][right]:
        	self._rec_cache_true(role, obj, rig, all, False)

    def _role_check(self, role, list, all):
        for object, right in list:
            if self._cache_get(role, object, right):
            	return True
        for object, right in list:
            si = self._single_check(role, object, right)
            if si:
            	self._rec_cache_true(role, object, right, all)
            	return True
            else:
                self._cache_set(role, object, right, False)

    #@Argument('roleset', type=RoleSet)
    @Argument('role', type=Role)
    @Argument('object', type=Entity)
    @Argument('right', type=str)
    def __call__(self, role, object, right):
        perf.begin('check')
        list, all = self._inherit_all(object, right)
        c = connection.cursor()
        c.callproc('test_perms', [str(role.id), permarg_list([(str(obj.id), right) for obj, right in list])])
        perf.end('check')
        return bool(c.fetchall()[0][0])

        for role in roleset.roles:
            rr = self._cache_get(role, object, right)
            if rr:
                perf.end('check')
            	return True
            if rr is None:
            	ret = None
        if ret is None:
        	ret = False
            list, all = self._inherit_all(object, right)
            for role in roleset.roles:
                if self._role_check(role, list, all):
                	ret = True
        perf.end('check')
        return ret
