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
        login = vars['username']
        password = vars['password']
        try:
            token_container.set_token(Security.login(login=login, password=password))
        except:
            print d
            print lw_path
            follow(d,lw_path)['loginspace'][0]['status'] = ['failed']
        return GetLink(d,path)
