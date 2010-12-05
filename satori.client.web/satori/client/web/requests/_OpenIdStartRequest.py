# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request
from django.http import HttpResponse, HttpResponseRedirect

import urlparse
import urllib

class OpenIdStartRequest(Request):
    pathName = 'openid_start'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        back_to = vars.get('back_to', '')
        path = vars.get('path', '')
        lw_path = vars.get('lw_path', '')
        openid = vars['openid']
        d = ParseURL(back_to)
        finisher = request.build_absolute_uri()
        callback = urlparse.urlparse(finisher)
        qs = urlparse.parse_qs(callback.query)
        qs['back_to'] = (back_to,)
        qs['path'] = (path,)
        qs['lw_path'] = (lw_path,)
        query = []
        for key, vlist in qs.items():
            for value in vlist:
                query.append((key,value))
        query = urllib.urlencode(query)
        path = '/process.openid_finish'
        finisher = urlparse.urlunparse((callback.scheme, callback.netloc, path, callback.params, query, callback.fragment))
        try:
            res = OpenIdentity.start(openid=openid, return_to=finisher)
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
