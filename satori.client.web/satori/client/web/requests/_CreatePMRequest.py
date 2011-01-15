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
        try:
            fullts = TestSuite.filter(TestSuiteStruct(name=''))[0]
        except:
            tss = TestSuiteStruct(name='All tests '+str(datetime.now()),problem=problem,dispatcher='SerialDispatcher',accumulators='StatusAccumulator')
            tl = Test.filter(TestStruct(problem=problem))
            tl.sort(key=lambda t : t.name)
            fullts = TestSuite.create(fields=tss,test_list=tl)
        ProblemMapping.create(ProblemMappingStruct(contest=contest, problem=problem,code=request.POST['code'], title=request.POST['title'],default_test_suite=fullts))
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
    
