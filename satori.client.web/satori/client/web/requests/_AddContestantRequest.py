# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class AddContestantRequest(Request):
    pathName = 'addcontestant'
    @classmethod
    def process(cls, request):
        d = ParseURL(request.POST['back_to'])
#        try:
        c = Contest.filter({'id':int(request.POST['cid'])})[0]
        u = User.filter({'login': request.POST['login']})[0]
#        except:
#            return GetLink(d,'')
        t = c.find_contestant(u)
        if not t:
            t = Contestant.create(fields=ContestantStruct(name=u.login,contest=c),user_list=[u])
        if request.POST['addrole']=='admin':
            c.add_admin(u)
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
