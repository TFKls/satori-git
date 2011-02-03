# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common import want_import
want_import(globals(), '*')
from _Request import Request

class AlterSuiteRequest(Request):
    pathName = 'altersuite'
    @classmethod
    def process(cls, request):
        if request.POST['id']:
            ts = TestSuite.filter(TestSuiteStruct(id=int(request.POST['id'])))[0]
        else:
            ts = None
            problem = Problem.filter(ProblemStruct(id=int(request.POST['problem'])))[0]
        tests = []
        for k in request.POST.keys():
            if k[0:4] == 'test':
                t = Test.filter({'id':int(k[4:])})[0]
                tests.append(t)
        name = request.POST['name']
        description = request.POST['description']
        reporter = request.POST['reporter']
        accumulators = []
        for k in request.POST.keys():
            if k[:4]=='acc_':
                accumulators.append(k[4:])
        tsstruct = TestSuiteStruct(name=name,description=description,reporter=reporter,accumulators=','.join(accumulators))
        if not ts:
            tsstruct.problem = problem
            tsstruct.dispatcher='SerialDispatcher'
        if ts:
            ts.modify_full(tsstruct,tests)
        else:
            TestSuite.create(tsstruct,tests)
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
