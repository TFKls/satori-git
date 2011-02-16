# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from django.conf import settings
from satori.client.web.librecaptcha import *
from satori.client.common import want_import
want_import(globals(), '*')
from _Request import Request
import traceback

class RegisterRequest(Request):
    pathName = 'register'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        d = ParseURL(vars.get('back_to', ''))
        path = vars.get('path', '')
        login = vars['login']
        password = vars['password']
        confirm = vars['confirm']
        firstname = vars['firstname']
        lastname = vars['lastname']
        affiliation = vars['affiliation']
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
                om = OaMap()
                om.set_str('affiliation',affiliation)
                u = User.register(UserStruct(login=login, email=email, firstname=firstname, lastname=lastname), password=password, profile=om.get_map())
            except InvalidLogin:
                error = 'badlogin'
            except InvalidPassword:
                error = 'badpass'
            except InvalidEmail:
                error = 'bademail'
            except:
                error = 'regfail'
                traceback.print_exc()
        if error:
            return GetLink(DefaultLayout(maincontent='registerform',status=[error]),'')
        else:
            return GetLink(DefaultLayout(maincontent='loginform',status=['waiting']),'')
