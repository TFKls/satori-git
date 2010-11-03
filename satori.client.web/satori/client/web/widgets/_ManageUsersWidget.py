# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

class ManageUsersWidget(Widget):
    pathName = 'manusers'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/manusers.html'
        c = ActiveContest(params)
        self.contest = c
        self.accepted = list()
        self.pending = list()
        self.back_to = ToString(params)
        self.path = path
        authenticated = Security.authenticated()
        if Privilege.get(authenticated, c, 'JOIN') is not None:
        	jo = 2
        elif Privilege.get(authenticated, c, 'APPLY') is not None:
            jo = 1
        else:
        	jo = 0
        self.joining_options=[["no_joining","Only when added",jo==0],["moderated","By acceptation",jo==1],["public","Freely",jo==2]]
        self.anonymous_view = Privilege.get(Security.anonymous(), c, 'VIEW') is not None
        
        for contestant in c.get_contestants().contestants:
            q = {}
            q['c'] = contestant.contestant
            q['name'] = contestant.name
            q['members'] = contestant.members
            if contestant.admin:
                q['admin'] = 'Admin'
            self.accepted.append(q)
        for contestant in c.get_pending_contestants().contestants:
            q = {}
            q['c'] = contestant.contestant
            q['name'] = contestant.name
            q['members'] = contestant.members
            if contestant.admin:
                q['admin'] = 'Admin'
            self.pending.append(q)
