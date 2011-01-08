# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class CreateProblemRequest(Request):
    pathName = 'createproblem'
    @classmethod
    def process(cls, request):
        p = Problem.create(ProblemStruct(name=request.POST['name']))
        p.description = request.POST['description']
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
