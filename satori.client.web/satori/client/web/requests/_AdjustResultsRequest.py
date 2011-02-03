# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common import want_import
want_import(globals(), '*')
from _Request import Request

class AdjustResultsRequest(Request):
    pathName = 'adjustresult'
    @classmethod
    def process(cls, request):
        d = ParseURL(request.POST['back_to'])
        p = request.POST['back_path']
        d2 = follow(d,p)
        sel = request.POST['user']
        if sel:
            d2['user'] = [sel]        
        return GetLink(d,'')
