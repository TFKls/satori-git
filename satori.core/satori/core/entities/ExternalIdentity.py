# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev import Events

from satori.core.models import Entity, User

#from satori.core.sec.openid import OpenIdentity
#from satori.core.sec.cas import CentralAuthenticationService

from types import NoneType
import string
import random
import urlparse
import urllib

ExternalIdentityFailed = DefineException('ExternalIdentityFailed', 'External Identity Authorization failed: {reason}',
    [('reason', unicode, False)])
InvalidExternalIdentityHandler = DefineException('InvalidExternalIdentityHandler', 'The specified hendler \'{handler}\' is invalid: {reason}',
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

    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_externalidentity')
    
    handler  = models.CharField(max_length=16)
    provider = models.CharField(max_length=512)
    identity = models.CharField(max_length=512, unique=True)

    user     = models.ForeignKey('User', related_name='authorized_identities')

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
            for key, value in data.items():
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

        Handler = None
        if handler == 'openid':
            Handler = OpenIdentity
        elif handler == 'cas' or handler == 'cas1' or handler == 'cas2' or handler == 'cas3':
            Handler = CentralAuthenticationService
        else:
            raise InvalidExternalIdentityHandler(handler=handler, reason='handler is not recognized')
        result = Handler.start(eid_session)

        session = Session.start()
        data = session.data_pickle
        if data is None:
            data = {}
        data[salt] = oid_session
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

        Handler = None
        if handler == 'openid':
            Handler = OpenIdentity
        elif handler == 'cas' or handler == 'cas1' or handler == 'cas2' or handler == 'cas3':
            Handler = CentralAuthenticationService
        else:
            raise InvalidExternalIdentityHandler(handler=handler, reason='handler is not recognized')
        result = Handler.finish(eid_session, callback, arg_map)

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
            identity = ExternalIdentity(handler=handler, provider=provider, identity=response.identity)
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
            if '_result' in data[key]:
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
        if '_type' not in oid_session or oid_session['_type'] != 'external_identity' or '_result' not in eid_session:
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
