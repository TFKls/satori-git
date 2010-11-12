# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request
from django.http import HttpResponse, HttpResponseRedirect

import urlparse
import urllib

class OpenIdRegisterRequest(Request):
    pathName = 'openid_register'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        d = ParseURL(vars.get('back_to', ''))
        path = vars.get('path', '')
        lw_path = vars['lw_path']
        openid = vars['openid']
        login = vars['username']
        finisher = request.build_absolute_uri()
        callback = urlparse.urlparse(finisher)
        qs = urlparse.parse_qs(callback.query)
        qs['back_to'] = (vars['back_to'],)
        qs['path'] = (vars['path'],)
        qs['lw_path'] = (vars['lw_path'],)
        query = []
        for key, vlist in qs.items():
            for value in vlist:
                query.append((key,value))
        query = urllib.urlencode(query)
        path = '/process.openid_confirm'
        finisher = urlparse.urlunparse((callback.scheme, callback.netloc, path, callback.params, query, callback.fragment))
        try:
            res = OpenIdentity.register_start(openid=openid, return_to=finisher, login=login)
            token_container.set_token(res['token'])
            if res['html']:
                ret = HttpResponse()
                ret.write(res['html'])
                return ret
            else:
                return HttpResponseRedirect(res['redirect'])
        except:
            follow(d,lw_path)['status'] = ['failed']
        return GetLink(d, path)
