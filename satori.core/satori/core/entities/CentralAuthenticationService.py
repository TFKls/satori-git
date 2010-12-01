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

CASRedirect = Struct('CASRedirect', (
    ('token', unicode, False),
    ('redirect', unicode, True),
))

@ExportModel
class CentralAuthenticationService(Entity):

    parent_entity = models.OneToOneField(Entity, parent_link=True, related_name='cast_centralauthenticationservice')

    realm    = models.ForeignKey('CentralAuthenticationServiceRealm', related_name='centralauthenticationservices')
    identity = models.CharField(max_length=512)
    user     = models.ForeignKey('User', related_name='authorized_cass')

    email    = models.CharField(max_length=64, null=True)
    name     = models.CharField(max_length=64, null=True)

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
    def start(realm_name, return_to):
        salt = OpenIdentity.salt()
        try:
            realm = CentralAuthenticationServiceRealm.objects.get(name=realm_name)
        except CentralAuthenticationServiceRealm.DoesNotExist:
            raise CentralAuthenticationServiceFailed("Authorization failed.")
        cas_session = { 'satori.cas.salt' : salt, 'satori.cas.realm' : realm.id }
        callback = OpenIdentity.modify_callback(return_to, { 'satori.cas.salt' : salt })
        redirect = realm.login_url(callback)

        session = Session.start()
        data = session.data_pickle
        if data is None:
            data = {}
        data['cas'] = cas_session
        session.data_pickle = data
        session.save()

        return {
            'token' : str(token_container.token),
            'redirect' : redirect,
        }
    @ExportMethod(unicode, [unicode, TypedMap(unicode, unicode)], PCPermit(), [CentralAuthenticationServiceFailed])
    @staticmethod
    def finish(return_to, arg_map):
        session = Session.start()
        data = session.data_pickle
        if data is None or 'cas' not in data:
            raise CentralAuthenticationServiceFailed("Authorization failed.")
        cas_session = data['cas']
        realm = CentralAuthenticationServiceRealm.objects.get(id=cas_session['satori.cas.realm'])
        ticket = arg_map['ticket']
        if not OpenIdentity.check_callback(return_to, { 'satori.cas.salt' : cas_session['satori.cas.salt'] }):
            raise CentralAuthenticationServiceFailed("CAS failed.")
        cas_user, cas_info = realm.validate(return_to, ticket)
        try:
            identity = CentralAuthenticationService.objects.get(realm=realm, identity=cas_user)
            identity.get_info(cas_info)
            identity.save()
            session.login(identity.user, 'cas')
            del data['cas']
            session.data_pickle = data
            session.cas_ticket = ticket
            session.save()
            return str(token_container.token)
        except CentralAuthenticationService.DoesNotExist:
            if session.role is not None:
                try:
                    user = User.objects.get(id=session.role.id)
                    identity = CentralAuthenticationService(realm=realm, identity=cas_user, user=user)
                    identity.get_info(cas_info)
                    identity.save()
                    del data['cas']
                    session.data_pickle = data
                    session.save()
                    return str(token_container.token)
                except User.DoesNotExist:
                    raise CentralAuthenticationServiceFailed("Authorization failed.")
            else:
                identity = CentralAuthenticationService(realm=realm, identity=cas_user)
                identity.get_info(cas_info)
                oid_session = {
                        'realm' : identity.realm.id,
                        'identity' : identity.identity,
                        'email' : identity.email,
                        'name' : identity.name,
                }
                data['cas'] = oid_session;
                session.data_pickle = data
                session.save()
                return str(token_container.token)
    @staticmethod
    def handle_login(session):
        if session.auth == 'cas':
            return
        data = session.data_pickle
        if data and 'cas' in data:
            cas = data['cas']
            if 'realm' in cas and 'identity' in cas and 'email' in cas and 'name' in cas:
                try:
                    identity = CentralAuthenticationService(user=session.user, realm=CentralAuthenticationServiceRealm.get(id=cas['realm']), identity=cas['identity'], email=cas['email'], name=cas['name'])
                    identity.save()
                except:
                    pass
    
    def handle_logut(session):
        return None

class CentralAuthenticationServiceEvents(Events):
    model = CentralAuthenticationService
    on_insert = on_update = ['realm', 'identity', 'user']
    on_delete = []
