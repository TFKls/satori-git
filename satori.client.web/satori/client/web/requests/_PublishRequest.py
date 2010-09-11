# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from datetime import datetime
from _Request import Request

class PublishRequest(Request):
    pathName = 'publish'
    @classmethod
    def process(cls, request):
        for k in request.POST.keys():
            if k[0:2] == 'pr':
                pm = ProblemMapping.filter({'id':int(k[2:])})[0]
                c = pm.contest
                for priv in Privilege.filter({'object' : pm, 'role' : c.contestant_role, 'right' : 'SUBMIT' }):
                    priv.delete()
                pt = None;
                ht = None;
                if request.POST['pub_time']!='':
                    pt = datetime(request.POST['pub_time'])
                if request.POST['hide_time']!='':
                    ht = datetime(request.POST['hide_time'])
                Privilege.create({'object' : pm, 'role' : c.contestant_role, 'right' : 'SUBMIT', 'startOn' : pt, 'finishOn' : ht })
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
