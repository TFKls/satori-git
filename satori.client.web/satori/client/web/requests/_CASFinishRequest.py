# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class CASFinishRequest(Request):
    pathName = 'cas_finish'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        back_to = vars.get('back_to', '')
        path = vars.get('path', '')
        lw_path = vars.get('lw_path', '')
        d = ParseURL(back_to)
        try:
            res = CentralAuthenticationService.finish(arg_map=dict(request.REQUEST.items()), callback=request.build_absolute_uri())
            token_container.set_token(res['token'])
        except:
            follow(d,lw_path)['status'] = ['failed']
        return GetLink(d,path)
