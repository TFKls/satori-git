# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class EditRankingRequest(Request):
    pathName = 'editranking'
    @classmethod
    def process(cls, request):
        d = ParseURL(request.POST['back_to'])
        pv = request.POST
        c = None
        if 'cancel' in pv.keys():
            return GetLink(d,'');
        if 'add' in pv.keys():
            c = ContestById(pv['contest_id'])
            s = RankingStruct(name=pv['name'],aggregator=pv['aggregator'],is_public=False, contest=c)
            Ranking.create(s)
            
            return GetLink(d,'')
        m = Ranking.filter({'id' : int(pv['id'])})[0]
        if m and 'edit' in pv.keys():
            m.name = pv['name']
#            m.header = pv['content']
#            m.footer = pv['footer']
            m.aggregator = pv['aggregator']
            m.rejudge()
            return GetLink(d,'')
        if 'delete' in pv.keys():
            m.delete()
        return GetLink(d,'')
