# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request


class CreatePMRequest(Request):
    pathName = 'createpm'
    @classmethod
    def process(cls,request):
        contest = ContestById(int(request.POST['contest']))
        problem = Problem.filter({'id' : int(request.POST['problem'])})[0]
        fullts = TestSuite.create({'problem': problem, 'dispatcher': ''})
        for t in Test.filter({'problem' : problem}):
            TestMapping.create({'suite' : fullts, 'test' : t, 'order' : t.id})
        ProblemMapping.create( {'contest' : contest, 'problem' : problem, 'code' : request.POST['code'], 'title' : request.POST['title'],'default_test_suite' : fullts} )
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
    
