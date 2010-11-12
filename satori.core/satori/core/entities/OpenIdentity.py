# vim:ts=4:sts=4:sw=4:expandtab
#! module models

from django.db import models

from satori.core.export        import ExportMethod
from satori.core.export_django import ExportModel
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

@ExportModel
class OpenIdentity(Entity):

    __module__ = "satori.core.models"
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
    def modify_callback(url, salt):
        callback = urlparse.urlparse(url)
        qs = urlparse.parse_qs(callback.query)
        qs['satori.openid.salt'] = (salt,)
        query = []
        for key, vlist in qs.items():
            for value in vlist:
                query.append((key,value))
        query = urllib.urlencode(query)
        return urlparse.urlunparse((callback.scheme, callback.netloc, callback.path, callback.params, query, callback.fragment))
    @staticmethod
    def check_callback(url, salt):
        callback = urlparse.urlparse(url)
        qs = urlparse.parse_qs(callback.query)
        if 'satori.openid.salt' not in qs:
            return False
        if len(qs['satori.openid.salt']) != 1:
            return False
        return qs['satori.openid.salt'][0] == salt
    @staticmethod
    def add_ax(request):
        axr = oidax.FetchRequest()
        axr.add(oidax.AttrInfo('http://axschema.org/contact/country/home', 1, True, 'country'))
        axr.add(oidax.AttrInfo('http://axschema.org/contact/email', 1, True, 'email'))
        axr.add(oidax.AttrInfo('http://axschema.org/namePerson/first', 1, True, 'firstname'))
        axr.add(oidax.AttrInfo('http://axschema.org/namePerson/last', 1, True, 'lastname'))
        axr.add(oidax.AttrInfo('http://axschema.org/pref/language', 1, True, 'language'))
        request.addExtension(axr)
    def get_ax(self, response, update =False):
        try:
            axr = oidax.FetchResponse.fromSuccessResponse(response)
            self.country = axr.getSingle('http://axschema.org/contact/country/home', self.country)
            self.email = axr.getSingle('http://axschema.org/contact/email', self.email)
            self.language = axr.getSingle('http://axschema.org/pref/language', self.language)
            firstname = axr.getSingle('http://axschema.org/namePerson/first', None)
            lastname = axr.getSingle('http://axschema.org/namePerson/last', None)
            if firstname != None and lastname != None:
                self.name = firstname + ' ' + lastname
            self.save()
            if update:
                self.user.name = self.name
                self.user.save()
        except:
            traceback.print_exc()
            pass
    @staticmethod
    def generic_start(openid, return_to, user_id ='', valid =1, update =False):
        salt = OpenIdentity.salt()
        session = { 'satori.openid.salt' : salt }
        store = Store()
        request = consumer.Consumer(session, store).begin(openid)
        if update:
            OpenIdentity.add_ax(request)
        redirect = ''
        html = ''
        realm = OpenIdentity.realm(return_to)
        callback = OpenIdentity.modify_callback(return_to, salt)
        if request.shouldSendRedirect():
            redirect = request.redirectURL(realm, callback)
        else:
            form = request.formMarkup(realm, callback, False, {'id': 'satori_openid_form'})
            html = '<html><body onload="document.getElementById(\'satori_openid_form\').submit()">' + form + '</body></html>'
        token = Token(user_id=user_id, auth='openid', validity=timedelta(hours=valid), data=session)
        return {
            'token' : str(token),
            'redirect' : redirect,
            'html' : html
        }
    @staticmethod
    def generic_finish(token, args, return_to, user=None, update=False):
        if token.auth != 'openid':
            return token
        session = token.data
        store = Store()
        response = consumer.Consumer(session, store).complete(args, return_to)
        if response.status != consumer.SUCCESS:
            raise Exception("OpenID failed.")
        callback = response.getReturnTo()
        if not OpenIdentity.check_callback(callback, session['satori.openid.salt']):
            raise Exception("OpenID failed.")
        if user:
            identity = OpenIdentity(identity=response.identity_url, user=user)
            identity.save()
        else:
            identity = OpenIdentity.objects.get(identity=response.identity_url)
        identity.get_ax(response, update=update)
        token = Token(user=identity.user, auth='openid', validity=timedelta(hours=6))
        return str(token)

    OpenIdRedirect = Struct('OpenIdRedirect', (
        ('token', unicode, False),
        ('redirect', unicode, True),
        ('html', unicode, True)
    ))

    @ExportMethod(OpenIdRedirect, [unicode, unicode], PCPermit(), [OpenIdentityFailed])
    @staticmethod
    def authenticate_start(openid, return_to):
        return OpenIdentity.generic_start(openid=openid, return_to=return_to, user_id='')

    @ExportMethod(unicode, [unicode, TypedMap(unicode, unicode)], PCPermit(), [OpenIdentityFailed])
    @staticmethod
    def authenticate_finish(return_to, arg_map):
        return OpenIdentity.generic_finish(token_container.token, arg_map, return_to)

    @ExportMethod(OpenIdRedirect, [unicode, unicode, unicode], PCPermit(), [OpenIdentityFailed])
    @staticmethod
    def register_start(login, openid, return_to):
        res = OpenIdentity.generic_start(openid=openid, return_to=return_to, user_id='', update=True)
        User.register(login=login, password=OpenIdentity.salt(), name='Unknown')
        user = User.objects.get(login=login)
        token = Token(res['token'])
        session = token.data
        session['satori.openid.user'] = user.id
        token.data = session
        res['token'] = str(token)
        return res

    @ExportMethod(unicode, [unicode, TypedMap(unicode, unicode)], PCPermit(), [OpenIdentityFailed])
    @staticmethod
    def register_finish(return_to, arg_map):
        session = token_container.token.data
        user = User.objects.get(id=session['satori.openid.user'])
        return OpenIdentity.generic_finish(token_container.token, arg_map, return_to, user, update=True)

    @ExportMethod(OpenIdRedirect, [unicode, unicode, unicode], PCPermit(), [OpenIdentityFailed])
    @staticmethod
    def add_start(password, openid, return_to):
        user = Security.whoami_user()
        if user.check_password(password):
            res = OpenIdentity.generic_start(openid=openid, return_to=return_to, user_id=str(user.id))
            token = Token(res['token'])
            session = token.data
            session['satori.openid.user'] = user.id
            token.data = session
            res['token'] = str(token)
            return res
        raise OpenIdentityFailed("Authorization failed.")

    @ExportMethod(unicode, [unicode, TypedMap(unicode, unicode)], PCPermit(), [OpenIdentityFailed])
    @staticmethod
    def add_finish(return_to, arg_map):
        session = token_container.token.data
        user = User.objects.get(id=session['satori.openid.user'])
        return OpenIdentity.generic_finish(token_container.token, arg_map, return_to, user)

class OpenIdentityEvents(Events):
    model = OpenIdentity
    on_insert = on_update = ['identity', 'user']
    on_delete = []

