# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class ContestRightsRequest(Request):
    pathName = 'contestrights'
    @classmethod
    def process(cls, request):
        c = ContestById(request.POST['contest_id'])
        for rg in Privilege.filter({'object':c, 'role':Security.anonymous(), 'right':'VIEW'}):
            rg.delete()
        if 'anonymous_view' in request.POST.keys():
            Privilege.create({'object':c, 'role':Security.anonymous(), 'right':'VIEW'})
        for rg in Privilege.filter({'object':c, 'role':Security.authenticated()}):
            rg.delete()
        if request.POST['joining_by']=='moderated':
            Privilege.create({'object':c, 'role':Security.authenticated(), 'right':'APPLY'})
        if request.POST['joining_by']=='public':
            Privilege.create({'object':c, 'role':Security.authenticated(), 'right':'JOIN'})
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
