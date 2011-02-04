# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common import want_import
want_import(globals(), '*')
from datetime import datetime
from _Request import Request

class PublishRequest(Request):
    pathName = 'publish'
    @classmethod
    def process(cls, request):
        confirm = False
        stop = False
        hide = False
        if 'confirm' in request.POST.keys():
            confirm = True
        if 'hide' in request.POST.keys():
            hide = True
        if 'stop' in request.POST.keys():
            stop = True
        for k in request.POST.keys():
            if k[0:2] == 'pr':
                pm = ProblemMapping.filter({'id':int(k[2:])})[0]
                c = pm.contest
                pt = None;
                ht = None;
                if request.POST['pub_date']!='':
                    ptstring = request.POST['pub_date']
                    pt = datetime.strptime(ptstring,"%d-%m-%Y %H:%M:%S")
                if request.POST['hide_date']!='':
                    htstring = request.POST['hide_date']
                    ht = datetime.strptime(htstring,"%d-%m-%Y %H:%M:%S")
                if confirm:
                    Privilege.grant(c.contestant_role, pm, 'SUBMIT', PrivilegeTimes(start_on=pt, finish_on=ht))
                    Privilege.grant(c.contestant_role, pm, 'VIEW', PrivilegeTimes(start_on=pt))
                if stop:
                    Privilege.revoke(c.contestant_role, pm, 'SUBMIT')
                if hide:
                    Privilege.revoke(c.contestant_role, pm, 'VIEW')
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
