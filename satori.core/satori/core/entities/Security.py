# vim:ts=4:sts=4:sw=4:expandtab


from datetime import datetime, timedelta
from types import NoneType
import string
import random
import urlparse
import urllib


@ExportClass
class Security(object):

    @ExportMethod(DjangoStruct('Role'), [], PCPermit())
    @staticmethod
    def anonymous():
        return Global.get_instance().anonymous

    @ExportMethod(DjangoStruct('Role'), [], PCPermit())
    @staticmethod
    def authenticated():
        return Global.get_instance().authenticated

    @ExportMethod(DjangoStruct('Role'), [], PCPermit())
    @staticmethod
    def whoami():
        if not token_container.token.user_id:
            return None
        try:
            return Role.objects.get(id=token_container.token.user_id)
        except Role.DoesNotExist:
            return None

    @ExportMethod(DjangoStruct('User'), [], PCPermit())
    @staticmethod
    def whoami_user():
        if not token_container.token.user_id:
            return None
        try:
            return User.objects.get(id=token_container.token.user_id)
        except User.DoesNotExist:
            return None
