# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class LogoutRequest(Request):
    pathName = 'logout'
    @classmethod
    def process(cls, request):
        token_container.set_token('')
        return GetLink(DefaultLayout(),'')
