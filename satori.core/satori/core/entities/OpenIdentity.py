# vim:ts=4:sts=4:sw=4:expandtab

import logging
from django.db import models

from satori.core.dbev               import Events

from satori.core.models import Entity, User
from satori.core.sec import Token, Store

from datetime import datetime, timedelta
from types import NoneType
import string
import random
import urlparse
import urllib

from openid.consumer import consumer
from openid.extensions import sreg as oidsreg
from openid.extensions import pape as oidpape
from openid.extensions import ax as oidax

OpenIdFailed = DefineException('OpenIdFailed', 'Open Identity Authorization failed: {reason}',
    [('reason', unicode, False)])
InvalidOpenIdProvider = DefineException('InvalidOpenIdProvider', 'The specified provider \'{provider}\' is invalid: {reason}',
    [('provider', unicode, False), ('reason', unicode, False)])
InvalidOpenIdCallback = DefineException('InvalidOpenIdCallback', 'The specified callback parameters are invalid: {reason}',
    [('reason', unicode, False)])

OpenIdRedirect = Struct('OpenIdRedirect', (
    ('token', unicode, False),
    ('redirect', unicode, True),
    ('html', unicode, True)
))
OpenIdResult = Struct('OpenIdResult', (
    ('token', unicode, False),
    ('linked', bool, False),
    ('salt', unicode, True)
))

@ExportModel
class OpenIdentity(Entity):

    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_openidentity')
    
    provider = models.CharField(max_length=512)
    identity = models.CharField(max_length=512, unique=True)

    user     = models.ForeignKey('User', related_name='authorized_openids')

    country  = models.CharField(max_length=64, null=True)
    email    = models.CharField(max_length=64, null=True)
    name     = models.CharField(max_length=64, null=True)
    language = models.CharField(max_length=64, null=True)

    class ExportMeta(object):
        fields = [('provider', 'VIEW'), ('user', 'VIEW'), ('country', 'VIEW'), ('email', 'VIEW'), ('name', 'VIEW'), ('language', 'VIEW')]
    
    salt_param = 'satori.openid.salt'

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
    def add_ax(request):
        axr = oidax.FetchRequest()
        axr.add(oidax.AttrInfo('http://axschema.org/contact/country/home', 1, True, 'country'))
        axr.add(oidax.AttrInfo('http://axschema.org/contact/email', 1, True, 'email'))
        axr.add(oidax.AttrInfo('http://axschema.org/namePerson/first', 1, True, 'firstname'))
        axr.add(oidax.AttrInfo('http://axschema.org/namePerson/last', 1, True, 'lastname'))
        axr.add(oidax.AttrInfo('http://axschema.org/pref/language', 1, True, 'language'))
        request.addExtension(axr)
    def get_ax(self, response):
	    axr = oidax.FetchResponse.fromSuccessResponse(response)
        if axr is None:
            return
        self.country = axr.getSingle('http://axschema.org/contact/country/home', self.country)
        self.email = axr.getSingle('http://axschema.org/contact/email', self.email)
        self.language = axr.getSingle('http://axschema.org/pref/language', self.language)
        firstname = axr.getSingle('http://axschema.org/namePerson/first', None)
        lastname = axr.getSingle('http://axschema.org/namePerson/last', None)
        if firstname is not None and lastname is not None:
            self.name = firstname + ' ' + lastname
    @ExportMethod(OpenIdRedirect, [unicode, unicode], PCPermit(), [InvalidOpenIdProvider])
    @staticmethod
    def start(openid, return_to):
        salt = OpenIdentity.salt()
        realm = OpenIdentity.realm(return_to)
        oid_session = {
            '_type' : 'openid',
            '_provider' : openid,
        }
        callback = OpenIdentity.modify_callback(return_to, { OpenIdentity.salt_param : salt })
        store = Store()
        try:
            request = consumer.Consumer(oid_session, store).begin(openid)
        except DiscoveryFailure as df:
            raise InvalidOpenIdProvider(provider=openid, reason='discovery failed')

        OpenIdentity.add_ax(request)
        redirect = ''
        html = ''
        if request.shouldSendRedirect():
            redirect = request.redirectURL(realm, callback)
        else:
            form = request.formMarkup(realm, callback, False, {'id': 'satori_openid_form'})
            html = '<html><body onload="f=document.getElementById(\'satori_openid_form\'); if (f) { f.style.visibility = \'hidden\'; f.submit() }">' + form + '</body></html>'

        session = Session.start()
        data = session.data_pickle
        if data is None:
            data = {}
        data[salt] = oid_session
        session.data_pickle = data
        session.save()

        return {
            'token' : str(token_container.token),
            'redirect' : redirect,
            'html' : html
        }
    @ExportMethod(OpenIdResult, [unicode, TypedMap(unicode, unicode)], PCPermit(), [InvalidOpenIdCallback, OpenIdFailed])
    @staticmethod
    def finish(callback, arg_map):
        session = Session.start()
        if OpenIdentity.salt_param not in arg_map:
            raise InvalidOpenIdCallback(reason="'" + OpenIdentity.salt_param + "' not specified")
        salt = arg_map[OpenIdentity.salt_param]
        data = session.data_pickle
        if data is None or salt not in data:
            raise InvalidOpenIdCallback(reason="'" + OpenIdentity.salt_param + "'  has wrong value")
        oid_session = data[salt]
        if '_type' not in oid_session or oid_session['_type'] != 'openid':
            raise InvalidOpenIdCallback(reason="'" + OpenIdentity.salt_param + "'  has wrong value")
        store = Store()
        response = consumer.Consumer(oid_session, store).complete(arg_map, callback)
        if response.status == consumer.CANCEL:
            raise OpenIdFailed(reason='request was cancelled')
        if response.status == consumer.CANCEL:
            raise OpenIdFailed(reason=response.message)
        if response.status != consumer.SUCCESS:
            raise OpenIdFailed("authorization failed")
        callback = response.getReturnTo()
        if not OpenIdentity.check_callback(callback, { OpenIdentity.salt_param : salt }):
            raise InvalidOpenIdCallback(reason="'" + OpenIdentity.salt_param + "'  has wrong value")
        try:
            identity = OpenIdentity.objects.get(provider=oid_session['_provider'], identity=response.identity_url)
            identity.get_ax(response)
            identity.save()
            session.login(identity.user, 'openid')
            del data[salt]
            session.data_pickle = data
            session.save()
            return {
                'token' : str(token_container.token),
                'linked' : True,
            }
        except OpenIdentity.DoesNotExist:
            identity = OpenIdentity(provider=oid_session['_provider'], identity=response.identity_url)
            identity.get_ax(response)
            oid_session = {
                '_type' : 'openid',
                '_success' : {
                    'provider' : identity.provider,
                    'identity' : identity.identity,
                    'country' : identity.country,
                    'email' : identity.email,
                    'name' : identity.name,
                    'language' : identity.language,
                }
            }
            data[salt] = oid_session;
            session.data_pickle = data
            session.save()
            return {
                'token' : str(token_container.token),
                'linked' : False,
                'salt' : salt,
            }

    @ExportMethod(TypedList(DjangoStruct('OpenIdentity')), [], PCTokenIsUser(), [])
    @staticmethod
    def get_linked():
        session = Session.start()
        data = session.data_pickle
        ret = []
        return OpenIdentity.objects.filter(user=token_container.token.user)

    @ExportMethod(TypedMap(unicode, DjangoStruct('OpenIdentity')), [], PCTokenIsUser(), [])
    @staticmethod
    def get_ready():
        session = Session.start()
        data = session.data_pickle
        ret = {}
        if type(data) == type({}):
            for key, value in data.items():
                if type(value) == type({}) and '_type' in value and value['_type'] == 'openid' and '_success' in value:
                    oid = OpenIdentity(**value['_success'])
                    oid.user = token_container.token.user
                    oid.id = token_container.token.user.id
                    ret[str(key)] = oid
        return ret

    @ExportMethod(NoneType, [unicode], PCTokenIsUser(), [OpenIdFailed])
    @staticmethod
    def add(salt):
        session = Session.start()
        data = session.data_pickle
        if data is None or salt not in data:
            raise OpenIdFailed(reason="'salt' has wrong value")
        oid_session = data[salt]
        if '_type' not in oid_session or oid_session['_type'] != 'openid' or '_success' not in oid_session:
            raise OpenIdFailed(reason="'salt' has wrong value")
        identity = OpenIdentity(**oid_session['_success'])
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

class OpenIdentityEvents(Events):
    model = OpenIdentity
    on_insert = on_update = ['provider', 'identity', 'user']
    on_delete = []
