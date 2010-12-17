# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class ExternalIdentityFinishRequest(Request):
    pathName = 'exid_finish'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        back_to = vars.get('back_to', '')
        path = vars.get('path', '')
        lw_path = vars.get('lw_path', '')
        d = ParseURL(back_to)
        try:
            res = ExternalIdentity.finish(arg_map=dict(request.REQUEST.items()), callback=request.build_absolute_uri())
            token_container.set_token(res['token'])
            if not res['linked']:
                return '/cover%7C(content%7C(override%7C1,name%7Cidentities),headerspace%7C(name%7Cheader),name%7Cmain),name%7Ccover.'
        except:
            follow(d,lw_path)['status'] = ['failed']
        return GetLink(d,path)
