# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common import want_import
want_import(globals(), '*')
from _Request import Request

class AskQuestionRequest(Request):
    pathName = 'askquestion'
    @classmethod
    def process(cls, request):
        d = ParseURL(request.POST['back_to'])
#        try:
        c = Contest.filter({'id':int(request.POST['contest_id'])})[0]
        pt = request.POST['problem']
        if pt=='':
            problem = None
        else:
            problem = ProblemMapping.filter(ProblemMappingStruct(id=int(pt)))[0]
        Question.create(QuestionStruct(problem=problem,contest=c,content=request.POST['content']))
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
