# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common import want_import
want_import(globals(), '*')
from _Request import Request

class AlterPMRequest(Request):
    pathName = 'alterpm'
    @classmethod
    def process(cls, request):
        pm = ProblemMapping.filter({'id':int(request.POST['pm_id'])})[0]
        pm.statement = request.POST['statement']
        if 'pdfstatement' in request.FILES.keys():
            pdf = request.FILES['pdfstatement']
            writer = Blob.create(pdf.size)
            writer.write(pdf.read())
            phash = writer.close()
            pm.statement_files_set_blob_hash('pdf',phash)
        pm.code = request.POST['code']
        pm.title = request.POST['title']
        pm.default_test_suite = TestSuite.filter(TestSuiteStruct(id=int(request.POST['dts'])))[0]
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
