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
        ret = DefaultLayout(dict=d,maincontent='results')
        p = ProblemMapping.filter({'id' : int(request.POST['problem'])})[0]
        if not ('content' in request.FILES.keys()):
            raise "Empty submits not allowed!"
        submit = request.FILES['content']
        c = p.contest
        cid = c.id
        pid = p.id
#        cct = CurrentContestant
        Submit.create(SubmitStruct(problem=p), content=submit.read(), filename=submit.name)
        return GetLink(ret,'')
