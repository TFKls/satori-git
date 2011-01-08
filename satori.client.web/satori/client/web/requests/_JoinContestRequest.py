# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class JoinContestRequest(Request):
    pathName = 'join'
    @classmethod
    def process(cls, request):
        contest = ContestById(request.POST['contest_id'])
        contest.join()
        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
