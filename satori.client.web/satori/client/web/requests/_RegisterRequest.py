# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class RegisterRequest(Request):
    pathName = 'register'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        d = ParseURL(vars.get('back_to', ''))
        path = vars.get('path', '')
        login = vars['username']
        password = vars['password']
        fullname = vars['fullname']
        User.register(login=login, password=password, name=fullname)
        try:
            t = User.authenticate(login=login, password=password)
            token_container.set_token(t)
        except:
            pass
        return GetLink(d, path)
