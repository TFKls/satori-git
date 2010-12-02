# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class OpenIdDelRequest(Request):
    pathName = 'openid_del'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        back_to = vars.get('back_to', '')
        path = vars.get('path', '')
        lw_path = vars.get('lw_path', '')
        id = vars.get('id', '')
        d = ParseURL(back_to)
        try:
            o = OpenIdentity.filter({'id': int(id)})[0]
            o.delete()
        except:
            follow(d,lw_path)['status'] = ['failed']
        return GetLink(d,path)
