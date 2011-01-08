# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request
from datetime import datetime


class CreatePMRequest(Request):
    pathName = 'createpm'
    @classmethod
    def process(cls,request):
        contest = ContestById(int(request.POST['contest']))
        problem = Problem.filter({'id' : int(request.POST['problem'])})[0]
        tss = TestSuiteStruct(name='All tests '+str(datetime.now()),problem=problem,dispatcher='SerialDispatcher',accumulators='StatusAccumulator')
        fullts = TestSuite.create(tss,Test.filter(TestStruct(problem=problem)))
        ProblemMapping.create(ProblemMappingStruct(contest=contest, problem=problem,code=request.POST['code'], title=request.POST['title'],default_test_suite=fullts))
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
    
