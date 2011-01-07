# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class EditSubpageRequest(Request):
    pathName = 'editsubpage'
    @classmethod
    def process(cls, request):
        d = ParseURL(request.POST['back_to'])
        pv = request.POST
        c = None
        if 'cancel' in pv.keys():
            return GetLink(d,'');
        if 'add' in pv.keys():
            if 'order' in pv.keys():
                order = int(pv['order'])
            else:
                order = None
            c = ContestById(pv['contest_id'])
            s = SubpageStruct(name=pv['name'],content=pv['content'],is_announcement=False, order=order, contest=c)
            s.is_public = (pv['msgtype']=='public')
            Subpage.create_for_contest(s)
            return GetLink(d,'')
        m = Subpage.filter({'id' : int(pv['id'])})[0]
        if m and not m.is_announcement and 'edit' in pv.keys():
            m.name = pv['name']
            m.content = pv['content']
            m.order = int(pv['order'])
            return GetLink(d,'')
        if 'delete' in pv.keys():
            m.delete()
        return GetLink(d,'')
