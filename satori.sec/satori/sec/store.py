# vim:ts=4:sts=4:sw=4:expandtab

__all__ = (
    'Store',
)

from satori.core.settings import SECRET_KEY
from satori.sec.models import Nonce, Association
from django.db.models import F
from openid.store.interface import OpenIDStore
from openid.store.nonce import SKEW
from openid.association import Association as OpenIdAssociation
import base64
import hashlib
import time

class Store(OpenIDStore):
    
    def storeAssociation(self, server_url, association):
        try:
            Association.objects.filter(
                server_url = server_url,
                handle     = association.handle,
            ).update(
                secret     = base64.urlsafe_b64encode(association.secret),
                issued     = association.issued,
                lifetime   = association.lifetime,
                assoc_type = association.assoc_type,
            )
        except:
            assoc = Association(
                server_url = server_url,
                handle = association.handle,
                secret = base64.urlsafe_b64encode(association.secret),
                issued = association.issued,
                lifetime = association.lifetime,
                assoc_type = association.assoc_type,
            )
            assoc.save()
    
    def getAssociation(self, server_url, handle=None):
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
        h.update(SECRET_KEY)
        return h.hexdigest()[:self.AUTH_KEY_LEN]
    
    def isDumb(self):
        return False
