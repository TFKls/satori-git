# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common import want_import
want_import(globals(), '*')
from _Request import Request

class AnswerQuestionRequest(Request):
    pathName = 'answerquestion'
    @classmethod
    def process(cls, request):
        d = ParseURL(request.POST['back_to'])
#        try:
        q = Question.filter({'id':int(request.POST['id'])})[0]
        q.answer = request.POST['answer']
        if 'publish' in request.POST.keys():
            q2 = Question.create(QuestionStruct(problem=q.problem,contest=q.contest,content=q.content))
            q2.answer = q.answer
            Privilege.grant(q.contest.contestant_role,q2,'VIEW')
            Privilege.revoke(q.inquirer,q,'VIEW')
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
