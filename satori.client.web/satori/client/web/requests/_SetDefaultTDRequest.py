# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common import want_import
want_import(globals(), '*')
from _Request import Request

class SetDefaultTDRequest(Request):
    pathName = 'set_default_td'
    @classmethod
    def process(cls, request):
        p = Problem.filter({'id' : int(request.POST['id'])})[0]
        if not request.POST['default_judge']:
            p.default_test_data_delete('judge')
        else:
            p.default_test_data_set_blob_hash('judge',request.POST['default_judge'])
        d = ParseURL(request.POST['back_to'])
        if not 'valchange' in request.POST.keys():
            return GetLink(d,'')
        for name,value in request.POST.iteritems():
            if name[0:6]=="value_":
                p.default_test_data_set_str(name[6:],value)
        for name,f in request.FILES.iteritems():
            if not name+"_clear" in request.POST.keys():
                writer = Blob.create(f.size)
                writer.write(f.read())
                fhash = writer.close()
                p.default_test_data_set_blob_hash(name[5:],fhash)
        return GetLink(d,'')
