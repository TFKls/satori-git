# vim:ts=4:sts=4:sw=4:expandtab

from django.db import models

from satori.core.dbev          import Events

from satori.core.models import Entity, User, CentralAuthenticationServiceRealm, OpenIdentity
from satori.core.sec import Token, Store

from datetime import datetime, timedelta
from types import NoneType
import string
import random
import urlparse
import urllib
import traceback

CentralAuthenticationServiceFailed = DefineException('CentralAuthenticationServiceFailed', 'Authorization failed')

@ExportModel
class CentralAuthenticationService(Entity):

    __module__ = "satori.core.models"
    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_centralauthenticationservice')

    realm    = models.ForeignKey('CentralAuthenticationServiceRealm', related_name='centralauthenticationservices')
    identity = models.CharField(max_length=512, unique=True)
    user     = models.ForeignKey('User', related_name='authorized_cass')

    email    = models.CharField(max_length=64, null=True)
    name     = models.CharField(max_length=64, null=True)
    
    def get_ax(self, response, update =False):
        print response

    @staticmethod
    def generic_start(realm_name, return_to, user_id ='', valid =1):
        realm = CentralAuthenticationServiceRealm.objects.get(name=realm_name)
        salt = OpenIdentity.salt()
        session = { 'satori.cas.salt' : salt, 'satori.cas.realm' : realm.id }
        callback = OpenIdentity.modify_callback(return_to, { 'satori.cas.salt' : salt })
        redirect = realm.login_url(callback)
        token = Token(user_id=user_id, auth='cas', validity=timedelta(hours=valid), data=session)
        return {
            'token' : str(token),
            'redirect' : redirect,
        }
    @staticmethod
    def generic_finish(token, args, return_to, user=None, update=False):
        if token.auth != 'cas':
            return str(token)
        session = token.data
        realm = CentralAuthenticationServiceRealm.objects.get(id=session['satori.cas.realm'])
        ticket = args['ticket']
        if not OpenIdentity.check_callback(callback, { 'satori.cas.salt' : session['satori.cas.salt'] }):
            raise Exception("CAS failed.")
        response_raw = realm.validate_ticket(return_to, ticket)
        response = StringIO(response_raw)
        valid = response.readline()
        identity = response.readline()
        if valid != 'yes':
            raise CentralAuthenticationServiceFailed("Authorization failed.")
        if user:
            cas = CentralAuthenticationService(realm=realm, identity=identity, user=user)
            cas.save()
        else:
            cas = CentralAuthenticationService.objects.get(realm=realm, identity=identity)
        cas.handle_response(response_raw, update=update)
        token = Token(user=identity.user, auth='cas', validity=timedelta(hours=6))
        return str(token)

    CASRedirect = Struct('CASRedirect', (
        ('token', unicode, False),
        ('redirect', unicode, True),
    ))

    @ExportMethod(CASRedirect, [unicode, unicode], PCPermit(), [OpenIdentityFailed])
    @staticmethod
    def authenticate_start(realm_name, return_to):
        return CentralAuthenticationService.generic_start(realm_name=realm_name, return_to=return_to, user_id='')

    @ExportMethod(unicode, [unicode, TypedMap(unicode, unicode)], PCPermit(), [OpenIdentityFailed])
    @staticmethod
    def authenticate_finish(return_to, arg_map):
        return CentralAuthenticationService.generic_finish(token_container.token, arg_map, return_to)

    @ExportMethod(CASRedirect, [unicode, unicode, unicode], PCPermit(), [OpenIdentityFailed])
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

    @ExportMethod(CASRedirect, [unicode, unicode, unicode], PCPermit(), [OpenIdentityFailed])
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

class CentralAuthenticationServiceEvents(Events):
    model = CentralAuthenticationService
    on_insert = on_update = ['identity', 'user']
    on_delete = []

