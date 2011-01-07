# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class LoginRequest(Request):
    pathName = 'login'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        d = ParseURL(vars.get('back_to', ''))
        path = vars['path']
        lw_path = vars['lw_path']
        f = follow(d,lw_path)
        if 'status' in f.keys():
            del f['status']
        login = vars['username']
        password = vars['password']
        try:
            t = User.authenticate(login=login, password=password)
            token_container.set_token(t)
        except:
            f['status'] = ['failed']
        return GetLink(d,path)
