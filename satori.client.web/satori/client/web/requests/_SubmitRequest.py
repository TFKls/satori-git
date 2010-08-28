# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request
    
class SubmitRequest(Request):
    pathName = 'submit'
    @classmethod
    def process(cls, request):
        d = ParseURL(request.POST['back_to'])
        d['content'] = [{'name' : ['results']}]
        p = ProblemMapping(int(request.POST['problem']))
        c = Contestant(int(request.POST['cid']))
        s = Submit(problem = p, owner = c, shortstatus = "Waiting")
        return GetLink(d,'')
