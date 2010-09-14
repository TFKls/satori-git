# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class EditMessageRequest(Request):
    pathName = 'editmsg'
    @classmethod
    def process(cls, request):
        d = ParseURL(request.POST['back_to'])
        pv = request.POST
        if 'cancel' in pv.keys():
            return GetLink(d,'');
        if 'add' in pv.keys():
            if pv['msgtype']=='contest_only':
                c = ContestById(pv['contest_id'])
                MessageContest.create({'topic': pv['msgtopic'], 'contest': c, 'content' : pv['msgcontent']})
            else:
                mso = (pv['msgtype']=='mainscreen_only')
                MessageGlobal.create({'topic' : pv['msgtopic'], 'content' : pv['msgcontent'], 'mainscreenonly' : mso})
            return GetLink(d,'')
        m = None
        try:
            m = MessageGlobal.filter({'id' : int(pv['msgid'])})[0]
        except:
            m = MessageContest.filter({'id' : int(pv['msgid'])})[0]
        if 'edit' in pv.keys():
            m.topic = pv['msgtopic']
            m.content = pv['msgcontent']
            return GetLink(d,'')
        if 'delete' in pv.keys():
            m.delete()
            return GetLink(d,'')
