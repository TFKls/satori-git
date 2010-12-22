# vim:ts=4:sts=4:sw=4:expandtab

from django.db.models import F

from satori.core.models import Nonce, Association

import urlparse
import urllib
import urllib2
from xml.dom import minidom
import base64
import hashlib
import time

from openid.consumer import consumer
from openid.extensions import sreg as oidsreg
from openid.extensions import pape as oidpape
from openid.extensions import ax as oidax
from openid.store.interface import OpenIDStore
from openid.store.nonce import SKEW
from openid.association import Association as OpenIdAssociation

class IdentityHandlerStartResult(object):
    def __init__(self):
        super(IdentityHandlerStartResult, self).__init__()
        self.redirect = None
        self.html = None

class IdentityHandlerFinishResult(object):
    def __init__(self):
        super(IdentityHandlerFinishResult, self).__init__()
        self.identity = None
        self.email = None
        self.name = None

class IdentityHandlerBase(object):
    def __init__(self):
        super(IdentityHandlerBase, self).__init__()
    @staticmethod
    def handle():
        return []
    @staticmethod
    def start(session):
        return IdentityHandlerStartResult()
    @staticmethod
    def finish(session, callback, arg_map):
        return IdentityHandlerFinishResult()

class CentralAuthenticationService(IdentityHandlerBase):
    @staticmethod
    def handle():
        return [ 'cas', 'cas1', 'cas2', 'cas3' ]

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
                if resp[0].strip() != 'yes':
                    return (None, {})
                return (resp[1].strip(), {})
            elif self.version == self.CAS_VERSION_2_0:
                url = self.validate_url(service=service, ticket=ticket)
                resp = minidom.parse(urllib2.urlopen(url))
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
                resp = minidom.parse(urllib2.urlopen(urllib2.Request(url=url, data=post.toxml(), headers = {
                    'cache-control': 'no-cache',
                    'pragma': 'no-cache',
                    'accept': 'text/xml',
                    'content-type': 'text/xml',
                    })))
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
   
    @staticmethod
    def start(session):
        result = IdentityHandlerStartResult()
        version = CentralAuthenticationService.Realm.SAML_VERSION_1_1
        if session['_handler'] == 'cas1':
            version = CentralAuthenticationService.Realm.CAS_VERSION_1_0
        if session['_handler'] == 'cas2':
            version = CentralAuthenticationService.Realm.CAS_VERSION_2_0
        cas_realm = CentralAuthenticationService.Realm(session['_provider'], version)
        result.redirect = cas_realm.login_url(session['_callback'])
        return result

    @staticmethod
    def finish(session, callback, arg_map):
        result = IdentityHandlerFinishResult()
        if 'ticket' not in arg_map:
            return result
        ticket = arg_map['ticket']
        version = CentralAuthenticationService.Realm.SAML_VERSION_1_1
        if session['_handler'] == 'cas1':
            version = CentralAuthenticationService.Realm.CAS_VERSION_1_0
        if session['_handler'] == 'cas2':
            version = CentralAuthenticationService.Realm.CAS_VERSION_2_0
        cas_realm = CentralAuthenticationService.Realm(session['_provider'], version)
        cas_user, cas_info = cas_realm.validate(callback, ticket)
        result.identity = cas_user
        if cas_info is not None:
            result.email = cas_info.get('mail', result.email)
            result.email = cas_info.get('email', result.email)
            firstname = cas_info.get('imie', None)
            firstname = cas_info.get('first', firstname)
            lastname = cas_info.get('nazwisko', None)
            lastname = cas_info.get('last', lastname)
            if firstname is not None and lastname is not None:
                result.name = firstname + ' ' + lastname
        return result

class OpenIdentity(IdentityHandlerBase):
    @staticmethod
    def handle():
        return [ 'openid' ]

    class Store(OpenIDStore):

        def storeAssociation(self, server_url, association):
            print 'store: add', server_url, association
            try:
                assoc = Association.objects.get(
                    server_url = server_url,
                    handle     = association.handle,
                )
            except:
                assoc = Association(
                    server_url = server_url,
                    handle = association.handle,
                )
            assoc.secret = base64.urlsafe_b64encode(association.secret)
            assoc.issued = association.issued
            assoc.lifetime = association.lifetime
            assoc.assoc_type = association.assoc_type
            assoc.save()

        def getAssociation(self, server_url, handle=None):
            print 'store: get', server_url
            try:
                assoc = Association.objects.filter(
                    issued__gt = (int(time.time()) - F('lifetime')),
                    server_url = server_url
                )
                if handle is not None:
                    assoc = assoc.filter(handle = handle)
                assoc = assoc.order_by('-issued')[0]
                return OpenIdAssociation(
                    handle = assoc.handle,
                    secret = base64.urlsafe_b64decode(assoc.secret),
                    issued = assoc.issued,
                    lifetime = assoc.lifetime,
                    assoc_type = assoc.assoc_type,
                )
            except:
                return None

        def removeAssociation(self, server_url, handle):
            Association.objects.filter(
                server_url = server_url,
                handle = handle,
            ).delete()

        def useNonce(self, server_url, timestamp, salt):
            if abs(timestamp - time.time()) > SKEW:
                return False
            try:
                nonce = Nonce(
                    server_url = server_url,
                    timestamp = timestamp,
                    salt = salt,
                )
                nonce.save()
                return True
            except:
                return False

        def cleanupNonce(self):
            Nonce.objects.filter(
                timestamp__lt = (int(time.time()) - nonce.SKEW),
            ).delete()

        def cleanupAssociations(self):
            Association.objects.filter(
                issued__lt = (int(time.time()) - F('lifetime')),
            ).delete()

        def getAuthKey(self):
            h = hashlib.md5()
            h.update(settings.SECRET_KEY)
            return h.hexdigest()[:self.AUTH_KEY_LEN]

        def isDumb(self):
            return False

    @staticmethod
    def start(session):
        result = IdentityHandlerStartResult()
        store = OpenIdentity.Store()
        request = consumer.Consumer(session, store).begin(session['_provider'])
        axr = oidax.FetchRequest()
        #axr.add(oidax.AttrInfo('http://axschema.org/contact/country/home', 1, True, 'country'))
        axr.add(oidax.AttrInfo('http://axschema.org/contact/email', 1, True, 'email'))
        axr.add(oidax.AttrInfo('http://axschema.org/namePerson/first', 1, True, 'firstname'))
        axr.add(oidax.AttrInfo('http://axschema.org/namePerson/last', 1, True, 'lastname'))
        #axr.add(oidax.AttrInfo('http://axschema.org/pref/language', 1, True, 'language'))
        request.addExtension(axr)
        if request.shouldSendRedirect():
            result.redirect = request.redirectURL(session['_realm'], session['_callback'])
        else:
            form = request.formMarkup(session['_realm'], session['_callback'], False, {'id': 'satori_openid_form'})
            result.html = '<html><body onload="f=document.getElementById(\'satori_openid_form\'); if (f) { f.style.visibility = \'hidden\'; f.submit() }">' + form + '</body></html>'
        return result

    @staticmethod
    def finish(session, callback, arg_map):
        result = IdentityHandlerFinishResult()
        store = OpenIdentity.Store()
        response = consumer.Consumer(session, store).complete(arg_map, callback)
        if response.status != consumer.SUCCESS:
            return result
        result.identity = response.identity_url
        axr = oidax.FetchResponse.fromSuccessResponse(response)
        if axr is not None:
            result.email = axr.getSingle('http://axschema.org/contact/email', result.email)
            firstname = axr.getSingle('http://axschema.org/namePerson/first', None)
            lastname = axr.getSingle('http://axschema.org/namePerson/last', None)
            if firstname is not None and lastname is not None:
                result.name = firstname + ' ' + lastname
        return result

identity_handlers = {}
for item in globals().values():
    if isinstance(item, type) and issubclass(item, IdentityHandlerBase) and (item != IdentityHandlerBase):
        for handle in item.handle():
            identity_handlers[handle] = item
