# vim:ts=4:sts=4:sw=4:expandtab

import string
import random
import urlparse
import urllib
import traceback
from types import NoneType

from django.db import models

from satori.core.dbev   import Events
from satori.core.models import Association, Entity, Nonce, User

ExternalIdentityFailed = DefineException('ExternalIdentityFailed', 'External Identity Authorization failed: {reason}',
    [('reason', unicode, False)])
InvalidExternalIdentityHandler = DefineException('InvalidExternalIdentityHandler', 'The specified handler \'{handler}\' is invalid: {reason}',
    [('handler', unicode, False), ('reason', unicode, False)])
InvalidExternalIdentityProvider = DefineException('InvalidExternalIdentityProvider', 'The specified provider \'{provider}\' is invalid: {reason}',
    [('provider', unicode, False), ('reason', unicode, False)])
InvalidExternalIdentityCallback = DefineException('InvalidExternalIdentityCallback', 'The specified callback parameters are invalid: {reason}',
    [('reason', unicode, False)])

ExternalIdentityRedirect = Struct('ExternalIdentityRedirect', (
    ('token', unicode, False),
    ('redirect', unicode, True),
    ('html', unicode, True)
))
ExternalIdentityResult = Struct('ExternalIdentityResult', (
    ('token', unicode, False),
    ('linked', bool, False),
    ('salt', unicode, True)
))

@ExportModel
class ExternalIdentity(Entity):
    """
    """
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_externalidentity')

    handler  = models.CharField(max_length=128)
    provider = models.CharField(max_length=512)
    identity = models.CharField(max_length=512, unique=True)

    user     = models.ForeignKey('User', related_name='authorized_identities', on_delete=models.CASCADE)

    email    = models.CharField(max_length=64, null=True)
    name     = models.CharField(max_length=64, null=True)

    class ExportMeta(object):
        fields = [('handler', 'VIEW'), ('provider', 'VIEW'), ('user', 'VIEW'), ('email', 'VIEW'), ('name', 'VIEW')]
    
    salt_param = 'satori.external.identity'

    @staticmethod
    def salt():
        chars = string.letters + string.digits
        salt = ''
        for i in range(16):
            salt += random.choice(chars)
        return salt
    @staticmethod
    def realm(url):
        callback = urlparse.urlparse(url)
        return urlparse.urlunparse((callback.scheme, callback.netloc, '', '', '', ''))
    @staticmethod
    def modify_callback(url, mods):
        callback = urlparse.urlparse(url)
        qs = urlparse.parse_qs(callback.query)
        for key, val in mods.items():
            qs[key] = (val,)
        query = []
        for key, vlist in qs.items():
            for value in vlist:
                query.append((key,value))
        query = urllib.urlencode(query)
        return urlparse.urlunparse((callback.scheme, callback.netloc, callback.path, callback.params, query, callback.fragment))
    @staticmethod
    def check_callback(url, mods):
        callback = urlparse.urlparse(url)
        qs = urlparse.parse_qs(callback.query)
        for key,val in mods.items():
            if key not in qs:
                return False
            if len(qs[key]) != 1:
                return False
            if qs[key][0] != val:
                return False
        return True
    @staticmethod
    def search_sessions(session, search):
        res = []
        if type(session) == type({}):
            for key, value in session.items():
                if type(value) == type({}):
                    ok=True
                    for sk, sv in search.items():
                        if sk not in value or value[sk] != sv:
                            ok = False
                            break
                    if ok:
                        res.append(key)
        return res
    @ExportMethod(ExternalIdentityRedirect, [unicode, unicode, unicode], PCPermit(), [InvalidExternalIdentityProvider])
    @staticmethod
    def start(handler, provider, return_to):
        from satori.core.sec.identity import identity_handlers
        salt = ExternalIdentity.salt()
        realm = ExternalIdentity.realm(return_to)
        callback = ExternalIdentity.modify_callback(return_to, { ExternalIdentity.salt_param : salt })
        eid_session = {
            '_type' : 'external_identity',
            '_handler' : handler,
            '_provider' : provider,
            '_salt' : salt,
            '_realm' : realm,
            '_callback' : callback,
            '_result' : None,
        }

        Handler = identity_handlers.get(handler, None)
        if Handler is None:
            raise InvalidExternalIdentityHandler(handler=handler, reason='handler is not recognized')
        try:
            result = Handler.start(eid_session)
        except:
            raise InvalidExternalIdentityProvider(provider=provider, reason='failed to initialize authorization sequence')

        session = Session.start()
        data = session.data_pickle
        if data is None:
            data = {}
        data[salt] = eid_session
        session.data_pickle = data
        session.save()

        return {
            'token' : str(token_container.token),
            'redirect' : result.redirect,
            'html' : result.html
        }
    @ExportMethod(ExternalIdentityResult, [unicode, TypedMap(unicode, unicode)], PCPermit(), [InvalidExternalIdentityCallback, ExternalIdentityFailed])
    @staticmethod
    def finish(callback, arg_map):
        from satori.core.sec.identity import identity_handlers
        session = Session.start()
        if ExternalIdentity.salt_param not in arg_map:
            raise InvalidExternalIdentityCallback(reason="'" + ExternalIdentity.salt_param + "' not specified")
        salt = arg_map[ExternalIdentity.salt_param]
        data = session.data_pickle
        if data is None or salt not in data:
            raise InvalidExternalIdentityCallback(reason="'" + ExternalIdentity.salt_param + "'  has wrong value")
        eid_session = data[salt]
        if '_salt' not in eid_session or eid_session['_salt'] != salt:
            raise InvalidExternalIdentityCallback(reason="'" + ExternalIdentity.salt_param + "'  has wrong value")
        if '_handler' not in eid_session:
            raise InvalidExternalIdentityCallback(reason="'" + ExternalIdentity.salt_param + "'  has wrong value")
        handler = eid_session['_handler']
        if '_provider' not in eid_session: 
            raise InvalidExternalIdentityCallback(reason="'" + ExternalIdentity.salt_param + "'  has wrong value")
        provider = eid_session['_provider']
        if '_realm' not in eid_session:
            raise InvalidExternalIdentityCallback(reason="'" + ExternalIdentity.salt_param + "'  has wrong value")
        realm = eid_session['_realm']
        if realm != ExternalIdentity.realm(callback):
            raise InvalidExternalIdentityCallback(reason='callback realm mismatch')
        if not ExternalIdentity.check_callback(callback, { ExternalIdentity.salt_param : salt }):
            raise InvalidExternalIdentityCallback(reason="'" + ExternalIdentity.salt_param + "'  has wrong value")

        Handler = identity_handlers.get(handler, None)
        if Handler is None:
            raise InvalidExternalIdentityHandler(handler=handler, reason='handler is not recognized')
        try:
            result = Handler.finish(eid_session, callback, arg_map)
        except:
            logging.exception('Handler.finish failed')
            raise InvalidExternalIdentityProvider(provider=provider, reason='failed to finalize authorization sequence')
        if result.identity is None:
            raise ExternalIdentityFailed(reason='authorization failed')

        for key in ExternalIdentity.search_sessions(data, {
                '_type' : 'external_identity',
                '_handler' : handler,
                '_provider' : provider,
            }):
            del data[key]

        try:
            identity = ExternalIdentity.objects.get(handler=handler, provider=provider, identity=result.identity)
            if result.email:
                identity.email = result.email
            if result.name:
                identity.name = result.name
            session.login(identity.user, 'external')
            session.data_pickle = data
            session.save()
            return {
                'token' : str(token_container.token),
                'linked' : True,
            }
        except ExternalIdentity.DoesNotExist:
            identity = ExternalIdentity(handler=handler, provider=provider, identity=result.identity)
            if result.email:
                identity.email = result.email
            if result.name:
                identity.name = result.name
            eid_session = {
                '_type' : 'external_identity',
                '_handler' : handler,
                '_provider' : provider,
                '_salt' : salt,
                '_realm' : realm,
                '_callback' : callback,
                '_result' : {
                    'handler' : identity.handler,
                    'provider' : identity.provider,
                    'identity' : identity.identity,
                    'email' : identity.email,
                    'name' : identity.name,
                }
            }
            data[salt] = eid_session;
            session.data_pickle = data
            session.save()
            return {
                'token' : str(token_container.token),
                'linked' : False,
                'salt' : salt,
            }

    @ExportMethod(TypedList(DjangoStruct('ExternalIdentity')), [], PCTokenIsUser(), [])
    @staticmethod
    def get_linked():
        session = Session.start()
        data = session.data_pickle
        ret = []
        return ExternalIdentity.objects.filter(user=token_container.token.user)

    @ExportMethod(TypedMap(unicode, DjangoStruct('ExternalIdentity')), [], PCTokenIsUser(), [])
    @staticmethod
    def get_ready():
        session = Session.start()
        data = session.data_pickle
        ret = {}
        for key in ExternalIdentity.search_sessions(data, {
                '_type' : 'external_identity',
            }):
            if '_result' in data[key] and data[key]['_result'] is not None:
                identity = ExternalIdentity(**data[key]['_result'])
                identity.user = token_container.token.user
                identity.id = token_container.token.user.id
                ret[str(key)] = identity
        return ret

    @ExportMethod(NoneType, [unicode], PCTokenIsUser(), [ExternalIdentityFailed])
    @staticmethod
    def add(salt):
        session = Session.start()
        data = session.data_pickle
        if data is None or salt not in data:
            raise ExternalIdentityFailed(reason="'salt' has wrong value")
        eid_session = data[salt]
        if '_type' not in eid_session or eid_session['_type'] != 'external_identity' or '_result' not in eid_session:
            raise ExternalIdentityFailed(reason="'salt' has wrong value")
        del data[salt]
        identity = ExternalIdentity(**eid_session['_result'])
        identity.user = token_container.token.user
        identity.save()
        Privilege.grant(identity.user, identity, 'MANAGE')
        session.data_pickle = data
        session.save()

    @staticmethod
    def handle_logout(session):
        return []

class ExternalIdentityEvents(Events):
    model = ExternalIdentity
    on_insert = on_update = ['handler', 'provider', 'identity', 'user']
    on_delete = []
