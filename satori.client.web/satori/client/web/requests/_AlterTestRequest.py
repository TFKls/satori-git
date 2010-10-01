# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class AlterTestRequest(Request):
    pathName = 'altertest'
    @classmethod
    def process(cls, request):
        d = ParseURL(request.POST['back_to'])
        path = request.POST['back_path']
        d2 = follow(d,path)
        if not 'valchange' in request.POST.keys():
            if request.POST['judge']:
                d2['judge'] = [request.POST['judge']]
            return GetLink(d,'')
        if 'testid' in request.POST.keys():
            ot = Test.filter({'id' : int(request.POST['testid'])})[0]
            p = t.problem
            t = Test.create({'problem' : p,'name' : p.name, 'description' : p.description})
        else:
            p = Problem.filter({'id' : int(request.POST['id'])})[0]
            t = Test.create({'problem' : p,'name' : request.POST['testname'],'description' : request.POST['testdesc']})
        t.oa_set_blob_hash('judge',request.POST['judge'])
        for name,value in request.POST.iteritems():
            if name[0:6]=="value_":
                t.oa_set_str(name[6:],value)
        for name,f in request.FILES.iteritems():
            if not name+"_clear" in request.POST.keys():
                writer = anonymous_blob(f.size)
                writer.write(f.read())
                fhash = writer.close()
                t.oa_set_blob_hash(name[5:],fhash)
        return GetLink(DefaultLayout(dict=d,maincontent='editproblem',problemid=[str(p.id)]),'')
