# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev          import Events

from satori.core.models import Entity

import urllib
import urllib2
import urlparse
from xml.dom import minidom

@ExportModel
class CentralAuthenticationServiceRealm(Entity):

    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_centralauthenticationservicerealm')

    name          = models.CharField(max_length=64, unique=True)
    base_url      = models.CharField(max_length=128, unique=True)

	CAS_VERSION_1_0 = 1
	CAS_VERSION_2_0 = 2
    SAML_VERSION_1_1 = 3

    version       = models.IntegerField()

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
                ret += Client._xml_find(node, tags[1:])
            return ret
        else:
            return [xml_node]
        
    def validate(self, service, ticket):
        ticket = str(ticket)
        if ticket[0:3] != 'ST-':
            raise ClientException("Ticket '%s' is ill-formed" % (ticket,))
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

class CentralAuthenticationServiceRealmEvents(Events):
    model = CentralAuthenticationServiceRealm
    on_insert = on_update = ['name', 'base_url']
    on_delete = []
