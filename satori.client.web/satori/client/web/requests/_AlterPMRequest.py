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
        pm.statement_set_str('text',request.POST['statement'])
        if 'pdfstatement' in request.FILES.keys():
            pdf = request.FILES['pdfstatement']
            writer = anonymous_blob(pdf.size)
            writer.write(pdf.read())
            phash = writer.close()
            pm.statement_set_blob_hash('pdf',phash)
        pm.code = request.POST['code']
        pm.title = request.POST['title']
        pm.default_test_suite = TestSuite.filter(TestSuiteStruct(id=int(request.POST['dts'])))[0]
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
