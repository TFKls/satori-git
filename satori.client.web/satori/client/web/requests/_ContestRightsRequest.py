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

        if request.POST['joining_by'] == 'public':
            Privilege.grant(authenticated, c, 'JOIN')
            Privilege.revoke(authenticated, c, 'APPLY')
            Privilege.grant(authenticated, c, 'VIEW')
        elif request.POST['joining_by'] == 'moderated':
            Privilege.revoke(authenticated, c, 'JOIN')
            Privilege.grant(authenticated, c, 'APPLY')
            Privilege.grant(authenticated, c, 'VIEW')
        elif request.POST['joining_by'] == 'invitation':
            Privilege.revoke(authenticated, c, 'APPLY')
            Privilege.revoke(authenticated, c, 'JOIN')
            Privilege.grant(authenticated, c, 'VIEW')
        else:
            Privilege.revoke(authenticated, c, 'APPLY')
            Privilege.revoke(authenticated, c, 'JOIN')
            Privilege.revoke(authenticated, c, 'VIEW')

        if request.POST['questions_for'] == 'everyone':
            Privilege.revoke(c.contestant_role, c, 'ASK_QUESTIONS')
            Privilege.grant(authenticated, c, 'ASK_QUESTIONS')
        elif request.POST['questions_for'] == 'contestants':
            Privilege.grant(c.contestant_role, c, 'ASK_QUESTIONS')
            Privilege.revoke(authenticated, c, 'ASK_QUESTIONS')
        else:
            Privilege.revoke(c.contestant_role, c, 'ASK_QUESTIONS')
            Privilege.revoke(authenticated, c, 'ASK_QUESTIONS')

        d = ParseURL(request.POST['back_to'])
        return GetLink(d,'')
