# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev          import Events

from satori.core.models import Entity, User, OpenIdentity
from satori.core.sec import Token, Store

from datetime import datetime, timedelta
from types import NoneType
import string
import random
import urlparse
import urllib
import traceback

CentralAuthenticationServiceFailed = DefineException('CentralAuthenticationServiceFailed', 'Authorization failed')
CASFailed = DefineException('CASFailed', 'CAS Authorization failed: {reason}',
    [('reason', unicode, False)])
InvalidCASProvider = DefineException('InvalidCASProvider', 'The specified provider \'{provider}\' is invalid: {reason}',
    [('provider', unicode, False), ('reason', unicode, False)])
InvalidCASCallback = DefineException('InvalidCASCallback', 'The specified callback parameters are invalid: {reason}',
    [('reason', unicode, False)])

CASRedirect = Struct('CASRedirect', (
    ('token', unicode, False),
    ('redirect', unicode, True),
))
CASResult = Struct('CASResult', (
    ('token', unicode, False),
    ('linked', bool, False),
    ('salt', unicode, True)
))

@ExportModel
class CentralAuthenticationService(Entity):

    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_centralauthenticationservice')

    provider = models.CharField(max_length=512)
    identity = models.CharField(max_length=512)
    
    user     = models.ForeignKey('User', related_name='authorized_cass')

    email    = models.CharField(max_length=64, null=True)
    name     = models.CharField(max_length=64, null=True)

    class ExportMeta(object):
        fields = [('provider', 'VIEW'), ('user', 'VIEW'), ('email', 'VIEW'), ('name', 'VIEW')]

    class Realm(object):
        CAS_VERSION_1_0 = 1
        CAS_VERSION_2_0 = 2
        SAML_VERSION_1_1 = 3

        def __init__(self, base_url, version = None):
            version = version or self.SAML_VERSION_1_1
            self.base_url = base_url
            self.version = version

        def modified_url(self, path_add, mods):
            callback = urlparse.urlparse(self.base_url)
            scheme = callback.scheme or 'https'
            path = callback.path.rstrip('/')
            qs = urlparse.parse_qs(callback.query)
            for key, val in mods.items():
                if val is None:
                    if key in qs:
                        del qs[key]
                else:
                    qs[key] = (val,)
            query = []
            for key, vlist in qs.items():
                for value in vlist:
                    query.append((key,value))
            query = urllib.urlencode(query)
            return urlparse.urlunparse((scheme, callback.netloc, path + path_add, callback.params, query, callback.fragment))

        def login_url(self, service, gateway=None, renew=None):
            if gateway:
                gateway = 'true'
            if renew:
                renew = 'true'
            return self.modified_url('/login', { 'service' : service, 'gateway' : gateway, 'renew' : renew })
        def logout_url(self):
            return self.modified_url('/logout', {})

        def validate_url(self, service, ticket=None, proxy=None):
            if self.version == self.CAS_VERSION_1_0:
                return self.modified_url('/validate', { 'service' : service, 'ticket' : ticket })
            elif self.version == self.CAS_VERSION_2_0:
                return self.modified_url('/serviceValidate', { 'service' : service, 'ticket' : ticket, 'pgtUrl' : proxy })
            elif self.version == self.SAML_VERSION_1_1:
                return self.modified_url('/samlValidate', { 'TARGET' : service })

        @staticmethod
        def _xml_find(xml_node, tags):
            print 'xml', xml_node, tags
            if len(tags) > 0:
                ret = []
                for node in xml_node.getElementsByTagNameNS('*', tags[0]):
                    ret += CentralAuthenticationService.Realm._xml_find(node, tags[1:])
                return ret
            else:
                return [xml_node]
            
        def validate(self, service, ticket):
            ticket = str(ticket)
            if ticket[0:3] != 'ST-':
                return (None, {})
            if self.version == self.CAS_VERSION_1_0:
                url = self.validate_url(service=service, ticket=ticket)
                resp = urllib2.urlopen(url).readlines()
                print resp
                if resp[0].strip() != 'yes':
                    return (None, {})
                return (resp[1].strip(), {})
            elif self.version == self.CAS_VERSION_2_0:
                url = self.validate_url(service=service, ticket=ticket)
                resp = minidom.parse(urllib2.urlopen(url))
                print resp.toxml()
                user = self._xml_find(resp, [ 'serviceResponse', 'authenticationSuccess', 'user' ])
                if len(user) < 1:
                    return (None, {})
                user =  ''.join([ child.toxml() for child in user[0].childNodes])
                return (user, {})
            elif self.version == self.SAML_VERSION_1_1:
                url = self.validate_url(service=service)
                impl = minidom.getDOMImplementation()
                post = impl.createDocument('http://schemas.xmlsoap.org/soap/envelope/', 'SOAP-ENV:Envelope', None)
                envelope = post.documentElement
                envelope.setAttribute('xmlns:SOAP-ENV', 'http://schemas.xmlsoap.org/soap/envelope/')
                envelope.appendChild(post.createElement('SOAP-ENV:Header'))
                body = post.createElement('SOAP-ENV:Body')
                envelope.appendChild(body)
                request = post.createElement('samlp:Request')
                request.setAttribute('xmlns:samlp', 'urn:oasis:names:tc:SAML:1.0:protocol')
                request.setAttribute('MajorVersion', '1')
                request.setAttribute('MinorVersion', '1')
                body.appendChild(request)
                artifact = post.createElement('samlp:AssertionArtifact')
                request.appendChild(artifact)
                artifact.appendChild(post.createTextNode(ticket))
                print url, post.toprettyxml()
                resp = minidom.parse(urllib2.urlopen(urllib2.Request(url=url, data=post.toxml(), headers = {
                    'cache-control': 'no-cache',
                    'pragma': 'no-cache',
                    'accept': 'text/xml',
                    'content-type': 'text/xml',
                    })))
                print resp.toprettyxml()
                user = self._xml_find(resp, [ 'Envelope', 'Body', 'Response', 'Assertion', 'AuthenticationStatement', 'NameIdentifier' ])
                if len(user) < 1:
                    return (None, {})
                user =  ''.join([ child.toxml() for child in user[0].childNodes])
                data = {}
                for node in self._xml_find(resp, [ 'Envelope', 'Body', 'Response', 'Assertion', 'AttributeStatement', 'Attribute' ]):
                    key = node.getAttribute('AttributeName')
                    value = self._xml_find(node, [ 'AttributeValue' ])
                    if len(value) < 1:
                        continue
                    value =  ''.join([ child.toxml() for child in value[0].childNodes])
                    data[key] = value
                return (user, data)
            return (None, {})

    def get_info(self, cas_info):
        if cas_info is None:
            return
        self.email = cas_info.get('mail', self.email)
        self.email = cas_info.get('email', self.email)
        firstname = cas_info.get('imie', None)
        firstname = cas_info.get('first', firstname)
        lastname = cas_info.get('nazwisko', None)
        lastname = cas_info.get('last', lastname)
        if firstname is not None and lastname is not None:
            self.name = firstname + ' ' + lastname
    
    @ExportMethod(CASRedirect, [unicode, unicode], PCPermit(), [CentralAuthenticationServiceFailed])
    @staticmethod
    def start(realm, return_to):
        salt = OpenIdentity.salt()
        cas_session = {
            '_type' : 'cas',
            '_provider' : realm,
        }
        callback = OpenIdentity.modify_callback(return_to, { OpenIdentity.salt_param : salt })
        try:
            cas_realm = CentralAuthenticationService.Realm(realm)
        except:
            raise InvalidCASProvider(provider=realm, reason='discovery failed')
        redirect = cas_realm.login_url(callback)

        session = Session.start()
        data = session.data_pickle
        if data is None:
            data = {}
        data[salt] = cas_session
        session.data_pickle = data
        session.save()

        return {
            'token' : str(token_container.token),
            'redirect' : redirect,
        }
    @ExportMethod(CASResult, [unicode, TypedMap(unicode, unicode)], PCPermit(), [CentralAuthenticationServiceFailed])
    @staticmethod
    def finish(callback, arg_map):
        session = Session.start()
        if OpenIdentity.salt_param not in arg_map:
            raise InvalidCASCallback(reason="'" + OpenIdentity.salt_param + "' not specified")
        salt = arg_map[OpenIdentity.salt_param]
        data = session.data_pickle
        if data is None or salt not in data:
            raise InvalidCASCallback(reason="'" + OpenIdentity.salt_param + "'  has wrong value")
        cas_session = data[salt]
        if '_type' not in cas_session or cas_session['_type'] != 'cas':
            raise InvalidCASCallback(reason="'" + OpenIdentity.salt_param + "'  has wrong value")
        if 'ticket' not in arg_map:
            raise InvalidCASCallback(reason="'ticket'  is not specified")
        ticket = arg_map['ticket']

        if not OpenIdentity.check_callback(callback, { OpenIdentity.salt_param : salt }):
            raise InvalidCASCallback(reason="'" + OpenIdentity.salt_param + "'  has wrong value")
        cas_realm = CentralAuthenticationService.Realm(cas_session['_provider'])
        cas_user, cas_info = cas_realm.validate(callback, ticket)
        try:
            identity = CentralAuthenticationService.objects.get(provider=cas_session['_provider'], identity=cas_user)
            identity.get_info(cas_info)
            identity.save()
            session.login(identity.user, 'cas')
            del data[salt]
            session.data_pickle = data
            session.cas_ticket = ticket
            session.save()
            return {
                'token' : str(token_container.token),
                'linked' : True,
            }
        except CentralAuthenticationService.DoesNotExist:
            identity = CentralAuthenticationService(provider=cas_session['_provider'], identity=cas_user)
            identity.get_info(cas_info)
            cas_session = {
                '_type' : 'cas',
                '_success' : {
                    'provider' : identity.provider,
                    'identity' : identity.identity,
                    'email' : identity.email,
                    'name' : identity.name,
                }
            }
            data[salt] = cas_session;
            session.data_pickle = data
            session.save()
            return {
                'token' : str(token_container.token),
                'linked' : False,
                'salt' : salt,
            }

    @ExportMethod(TypedList(DjangoStruct('CentralAuthenticationService')), [], PCTokenIsUser(), [])
    @staticmethod
    def get_linked():
        session = Session.start()
        data = session.data_pickle
        ret = []
        return CentralAuthenticationService.objects.filter(user=token_container.token.user)

    @ExportMethod(TypedMap(unicode, DjangoStruct('CentralAuthenticationService')), [], PCTokenIsUser(), [])
    @staticmethod
    def get_ready():
        session = Session.start()
        data = session.data_pickle
        ret = {}
        if type(data) == type({}):
            for key, value in data.items():
                if type(value) == type({}) and '_type' in value and value['_type'] == 'cas' and '_success' in value:
                    cas = CentralAuthenticationService(**value['_success'])
                    cas.user = token_container.token.user
                    cas.id = token_container.token.user.id
                    ret[str(key)] = cas
        return ret

    @ExportMethod(NoneType, [unicode], PCTokenIsUser(), [CASFailed])
    @staticmethod
    def add(salt):
        session = Session.start()
        data = session.data_pickle
        if data is None or salt not in data:
            raise CASFailed(reason="'salt' has wrong value")
        cas_session = data[salt]
        if '_type' not in cas_session or cas_session['_type'] != 'cas' or '_success' not in cas_session:
            raise CASFailed(reason="'salt' has wrong value")
        identity = CentralAuthenticationService(**cas_session['_success'])
        identity.user = token_container.token.user
        identity.save()
        Privilege.grant(identity.user, identity, 'MANAGE')
        del data[salt]
        session.data_pickle = data
        session.save()

    @staticmethod
    def handle_login(session):
        return None
    
    @staticmethod
    def handle_logut(session):
        return None


class CentralAuthenticationServiceEvents(Events):
    model = CentralAuthenticationService
    on_insert = on_update = ['realm', 'identity', 'user']
    on_delete = []
