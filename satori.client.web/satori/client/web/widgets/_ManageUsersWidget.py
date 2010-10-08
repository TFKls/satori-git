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
        for t in Contestant.filter({'contest':c}):
            q = {}
            q['c'] = t
            q['name'] = t.name_auto()
            q['members'] = t.members()
            for member in t.members():
                if Privilege.get(member,c,'MANAGE'):
                    q['admin'] = 'Admin'
            if t.accepted:
                self.accepted.append(q)
            else:
                self.pending.append(q)
