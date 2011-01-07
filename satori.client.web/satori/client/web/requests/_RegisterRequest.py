# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from django.conf import settings
from satori.client.web.librecaptcha import *
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
        confirm = vars['confirm']
        fullname = vars['fullname']
        email = vars['email']
        lw_path = vars['lw_path']
        remote_ip = request.META['REMOTE_ADDR']
        challenge = request.POST['recaptcha_challenge_field']
        response = request.POST['recaptcha_response_field']
        recaptcha_response = submit(challenge, response, settings.RECAPTCHA_PRIV_KEY, remote_ip)        
        error = False
        if password!=confirm:
            error = 'nomatch'
        elif not recaptcha_response.is_valid:
            error = 'captchafail'
        else:
            try:
                User.register(UserStruct(login=login, email=email, name=fullname), password=password)
            except InvalidLogin:
                error = 'badlogin'
            except InvalidPassword:
                error = 'badpass'
            except InvalidEmail:
                error = 'bademail'
            except:
                error = 'regfail'
        if error:
            return GetLink(DefaultLayout(maincontent='registerform',status=[error]),'')
        else:
            return GetLink(DefaultLayout(maincontent='loginform',status=['waiting']),'')
