# vim:ts=4:sts=4:sw=4:expandtab

import urlparse
import urllib
import urllib2
from xml.dom import minidom

class CentralAuthenticationService(object):

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
        version = CentralAuthenticationService.Realm.SAML_VERSION_1_1
        if session['_handler'] == 'cas1':
            version = CentralAuthenticationService.Realm.CAS_VERSION_1_0
        if session['_handler'] == 'cas2':
            version = CentralAuthenticationService.Realm.CAS_VERSION_2_0
        cas_realm = CentralAuthenticationService.Realm(session['_provider'], version)
        result = object()
        result.html = None
        result.redirect = cas_realm.login_url(session['_callback'])
        return result

    @staticmethod
    def finish(session, callback, arg_map):
        version = CentralAuthenticationService.Realm.SAML_VERSION_1_1
        if session['_handler'] == 'cas1':
            version = CentralAuthenticationService.Realm.CAS_VERSION_1_0
        if session['_handler'] == 'cas2':
            version = CentralAuthenticationService.Realm.CAS_VERSION_2_0
        cas_realm = CentralAuthenticationService.Realm(session['_provider'], version)
        cas_user, cas_info = cas_realm.validate(callback, ticket)
        result = object()
        result.identity = cas_user
        result.email = None
        result.name = None
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
