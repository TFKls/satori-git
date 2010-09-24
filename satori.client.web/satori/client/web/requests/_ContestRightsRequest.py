# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from django.db import models
from satori.client.common.remote import *
from _Request import Request

class ContestRightsRequest(Request):
    pathName = 'contestrights'
    @classmethod
    def process(cls, request):
        c = ContestById(request.POST['contest_id'])
        anonymous = Security.anonymous()
        authenticated = Security.authenticated()
        if 'anonymous_view' in request.POST.keys():
        	Privilege.grant(anonymous, c, 'VIEW')
        else:
            Privilege.revoke(anonymous, c, 'VIEW')

        if request.POST['joining_by'] == 'moderated':
        	Privilege.grant(authenticated, c, 'APPLY')
        	Privilege.revoke(authenticated, c, 'JOIN')
        elif request.POST['joining_by'] == 'public':
        	Privilege.revoke(authenticated, c, 'APPLY')
        	Privilege.grant(authenticated, c, 'JOIN')
        else:
        	Privilege.revoke(authenticated, c, 'APPLY')
        	Privilege.revoke(authenticated, c, 'JOIN')

        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
