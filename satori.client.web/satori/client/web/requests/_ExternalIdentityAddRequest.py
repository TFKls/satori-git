# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common import want_import
want_import(globals(), '*')
from _Request import Request

class ExternalIdentityAddRequest(Request):
    pathName = 'exid_add'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        back_to = vars.get('back_to', '')
        path = vars.get('path', '')
        lw_path = vars.get('lw_path', '')
        salt = vars.get('salt', '')
        d = ParseURL(back_to)
        try:
            ExternalIdentity.add(salt=salt)
        except:
            follow(d,lw_path)['status'] = ['failed']
        return GetLink(d,path)
