# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class AlterSuiteRequest(Request):
    pathName = 'altersuite'
    @classmethod
    def process(cls, request):
        pm = ProblemMapping.filter({'id':int(request.POST['pm_id'])})[0]
        dts = pm.default_test_suite
        nts = TestSuite.create({'problem ': pm.problem, 'dispatcher ': dts.dispatcher})
        for k in request.POST.keys():
            if k[0:4] == 'test':
                t = Test.filter({'id':int(k[4:])})[0]
                TestMapping.create({'test': t, 'suite': nts, 'order':t.id})
        pm.default_test_suite = nts
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
