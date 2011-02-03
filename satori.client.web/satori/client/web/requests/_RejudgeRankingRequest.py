# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common import want_import
want_import(globals(), '*')
from _Request import Request

class RejudgeRankingRequest(Request):
    pathName = 'rejudgeranking'
    @classmethod
    def process(cls, request):
        r = Ranking.filter({'id':int(request.POST['id'])})[0]
        r.rejudge()
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
