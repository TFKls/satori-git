# vim:ts=4:sts=4:sw=4:expandtab

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
import traceback

from openid.consumer import consumer
from openid.extensions import sreg as oidsreg
from openid.extensions import pape as oidpape
from openid.extensions import ax as oidax

OpenIdentityFailed = DefineException('OpenIdentityFailed', 'Invalid open identity')

OpenIdRedirect = Struct('OpenIdRedirect', (
    ('token', unicode, False),
    ('redirect', unicode, True),
    ('html', unicode, True)
))

@ExportModel
class OpenIdentity(Entity):

    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_openidentity')

    identity = models.CharField(max_length=512, unique=True)
    user     = models.ForeignKey('User', related_name='authorized_openids')

    country  = models.CharField(max_length=64, null=True)
    email    = models.CharField(max_length=64, null=True)
    name     = models.CharField(max_length=64, null=True)
    language = models.CharField(max_length=64, null=True)
    
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
    @ExportMethod(OpenIdRedirect, [unicode, unicode], PCPermit(), [OpenIdentityFailed])
    @staticmethod
    def start(openid, return_to):
        salt = OpenIdentity.salt()
        realm = OpenIdentity.realm(return_to)
        oid_session = { 'satori.openid.salt' : salt }
        callback = OpenIdentity.modify_callback(return_to, { 'satori.openid.salt' : salt })
        store = Store()
        request = consumer.Consumer(oid_session, store).begin(openid)
        OpenIdentity.add_ax(request)
        redirect = ''
        html = ''
        if request.shouldSendRedirect():
            redirect = request.redirectURL(realm, callback)
        else:
            form = request.formMarkup(realm, callback, False, {'id': 'satori_openid_form'})
            html = '<html><body onload="document.getElementById(\'satori_openid_form\').submit()">' + form + '</body></html>'

        session = Session.start()
        data = session.data_pickle
        if data is None:
            data = {}
        data['openid'] = oid_session
        session.data_pickle = data
        session.save()

        return {
            'token' : str(token_container.token),
            'redirect' : redirect,
            'html' : html
        }
    @ExportMethod(unicode, [unicode, TypedMap(unicode, unicode)], PCPermit(), [OpenIdentityFailed])
    @staticmethod
    def finish(return_to, arg_map):
        session = Session.start()
        data = session.data_pickle
        if data is None or 'openid' not in data:
            raise OpenIdentityFailed("Authorization failed.")
        oid_session = data['openid']
        store = Store()
        response = consumer.Consumer(oid_session, store).complete(arg_map, return_to)
        if response.status != consumer.SUCCESS:
            raise OpenIdentityFailed("Authorization failed.")
        callback = response.getReturnTo()
        if not OpenIdentity.check_callback(callback, { 'satori.openid.salt' : oid_session['satori.openid.salt'] }):
            raise OpenIdentityFailed("Authorization failed.")
        try:
            identity = OpenIdentity.objects.get(identity=response.identity_url)
            identity.get_ax(response)
            identity.save()
            session.login(identity.user, 'openid')
            del data['openid']
            session.data_pickle = data
            session.save()
            return str(token_container.token)
        except OpenIdentity.DoesNotExist:
            if session.role is not None:
                try:
                    user = User.objects.get(id=session.role.id)
                    identity = OpenIdentity(identity=response.identity_url, user=user)
                    identity.get_ax(response)
                    identity.save()
                    del data['openid']
                    session.data_pickle = data
                    session.save()
                    return str(token_container.token)
                except User.DoesNotExist:
                    raise OpenIdentityFailed("Authorization failed.")
            else:
                identity = OpenIdentity(identity=response.identity_url)
                identity.get_ax(response)
                oid_session = {
                        'identity' : identity.identity,
                        'country' : identity.country,
                        'email' : identity.email,
                        'name' : identity.name,
                        'language' : identity.language,
                }
                data['openid'] = oid_session;
                session.data_pickle = data
                session.save()
                return str(token_container.token)
    @staticmethod
    def handle_login(session):
        if session.auth == 'openid':
            return
        data = session.data_pickle
        if data and 'openid' in data:
            oid = data['openid']
            if 'identity' in oid and 'country' in oid and 'email' in oid and 'name' in oid and 'language' in oid:
                try:
                    identity = OpenIdentity(user=session.user, identity=oid['identity'], country=oid['country'], email=oid['email'], name=oid['name'], language=oid['language'])
                    identity.save()
                except:
                    pass
    
    def handle_logut(session):
        return None

class OpenIdentityEvents(Events):
    model = OpenIdentity
    on_insert = on_update = ['identity', 'user']
    on_delete = []
