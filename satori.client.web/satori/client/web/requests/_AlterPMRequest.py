# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class AlterPMRequest(Request):
    pathName = 'alterpm'
    @classmethod
    def process(cls, request):
        pm = ProblemMapping.filter({'id':int(request.POST['pm_id'])})[0]
        pm.statement = request.POST['statement']
        pm.code = request.POST['code']
        pm.title = request.POST['title']
        d = ParseURL(request.POST['back_to'])
        ret = DefaultLayout(dict=d,maincontent='problems')
        return GetLink(ret,'')
