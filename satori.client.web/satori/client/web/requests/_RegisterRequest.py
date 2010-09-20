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
        path = vars['path']
        login = vars['username']
        password = vars['password']
        fullname = vars['fullname']
        Security.register(login=login, password=password, fullname=fullname)
        return GetLink(d, path)
