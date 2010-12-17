# vim:ts=4:sts=4:sw=4:expandtab

from django.db.models import F

from satori.core.models import Nonce, Association

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

class OpenIdentity(object):

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
        store = OpenIdentity.Store()
        request = consumer.Consumer(session, store).begin(session['_provider'])
        axr = oidax.FetchRequest()
        #axr.add(oidax.AttrInfo('http://axschema.org/contact/country/home', 1, True, 'country'))
        axr.add(oidax.AttrInfo('http://axschema.org/contact/email', 1, True, 'email'))
        axr.add(oidax.AttrInfo('http://axschema.org/namePerson/first', 1, True, 'firstname'))
        axr.add(oidax.AttrInfo('http://axschema.org/namePerson/last', 1, True, 'lastname'))
        #axr.add(oidax.AttrInfo('http://axschema.org/pref/language', 1, True, 'language'))
        request.addExtension(axr)
        result = object()
        result.redirect = None
        result.html = None
        if request.shouldSendRedirect():
            result.redirect = request.redirectURL(realm, callback)
        else:
            form = request.formMarkup(realm, callback, False, {'id': 'satori_openid_form'})
            result.html = '<html><body onload="f=document.getElementById(\'satori_openid_form\'); if (f) { f.style.visibility = \'hidden\'; f.submit() }">' + form + '</body></html>'
        return result

    @staticmethod
    def finish(session, callback, arg_map):
        store = OpenIdentity.Store()
        response = consumer.Consumer(oid_session, store).complete(arg_map, callback)
        if response.status == consumer.CANCEL:
            raise OpenIdFailed(reason='request was cancelled')
        if response.status == consumer.CANCEL:
            raise OpenIdFailed(reason=response.message)
        if response.status != consumer.SUCCESS:
            raise OpenIdFailed("authorization failed")
        result = object()
        result.identity = response.identity_url
        result.email = None
        result.name = None
	    axr = oidax.FetchResponse.fromSuccessResponse(response)
        if axr is not None:
            result.email = axr.getSingle('http://axschema.org/contact/email', result.email)
            firstname = axr.getSingle('http://axschema.org/namePerson/first', None)
            lastname = axr.getSingle('http://axschema.org/namePerson/last', None)
            if firstname is not None and lastname is not None:
                result.name = firstname + ' ' + lastname
        return result
