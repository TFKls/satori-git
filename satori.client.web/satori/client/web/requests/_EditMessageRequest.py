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
        c = None
        if 'cancel' in pv.keys():
            return GetLink(d,'');
        if 'add' in pv.keys():
            s = SubpageStruct(name=pv['name'],content=pv['content'],is_announcement=True)
            if pv['msgtype']=='contest_only':
                c = ContestById(pv['contest_id'])
                s.contest = c
                glb = False
            if pv['msgtype']=='mainscreen_only':
                s.is_everywhere = False
                glb = True
            if pv['msgtype']=='global':
                s.is_everywhere = True
                glb = True
            if glb:
                Subpage.create_global(s)
            else:
                Subpage.create_for_contest(s)
            return GetLink(d,'')
        m = Subpage.filter({'id' : int(pv['id'])})[0]
        if m and m.is_announcement and 'edit' in pv.keys():
            m.name = pv['name']
            m.content = pv['content']
            return GetLink(d,'')
        if 'delete' in pv.keys():
            m.delete()
        return GetLink(d,'')
