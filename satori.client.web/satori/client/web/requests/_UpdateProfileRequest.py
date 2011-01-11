# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class UpdateProfileRequest(Request):
    pathName = 'updateprofile'
    @classmethod
    def process(cls, request):
        vars = request.REQUEST
        d = ParseURL(vars.get('back_to', ''))
        path = vars['back_path']
        f = follow(d,path)
        if 'status' in f.keys():
            del f['status']
        oldpass = vars['password']
        newpass = vars['newpass']
        confirmpass = vars['confirmpass']
        u = CurrentUser()
        error = None
        if newpass==confirmpass:
            try:
                u.change_password(old_password=oldpass,new_password=newpass)
                f['status'] = ['ok']
            except LoginFailed:
                error = 'loginfail'
            except InvalidPassword:
                error = 'passfail'
            except:
                error =' fail'
        else:
            error = 'nomatch'
        
#        try:
#            t = User.authenticate(login=login, password=password)
#            token_container.set_token(t)
#        except:
#            f['status'] = ['failed']
        if error:
            f['status'] = [error]
        return GetLink(d,'')
