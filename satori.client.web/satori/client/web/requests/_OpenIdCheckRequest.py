# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class OpenIdCheckRequest(Request):
    pathName = 'openid_check'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        back_to = vars.get('back_to', '')
        path = vars.get('path', '')
        lw_path = vars.get('lw_path', '')
        d = ParseURL(back_to)
        print dict(request.REQUEST.items())
        try:
            token_container.set_token(Security.openid_login_finish(arg_map=dict(request.REQUEST.items()), return_to=request.build_absolute_uri()))
        except:
            follow(d,lw_path)['status'] = ['failed']
        return GetLink(d,path)
