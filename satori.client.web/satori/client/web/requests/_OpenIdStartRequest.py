# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

import urlparse
import urllib

class OpenIdStartRequest(Request):
    pathName = 'openid_start'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        d = ParseURL(vars['back_to'])
        path = vars.get('path', '')
        lw_path = vars['lw_path']
        openid = vars['openid']
        finisher = request.build_absolute_uri()
        print finisher
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
        path = callback.path.split('.')
        path[-1] = 'openid_check'
        path = '.'.join(path)
        finisher = urlparse.urlunparse((callback.scheme, callback.netloc, path, callback.params, query, callback.fragment))
        print finisher
        try:
            res = Security.openid_login_start(openid=openid, return_to=finisher)
            token_container.set_token(res['token'])
            if res['html']:
                ret = HttpResponse()
                ret.write(res['html'])
                return ret;
            else:
                return HttpResponseRedirect(res['redirect'])
        except:
            follow(d,lw_path)['loginspace'][0]['status'] = ['failed']
