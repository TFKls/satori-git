from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common import *
from satori.client.web.widgets import Widget

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
        jo = 0
        if explicit_right(c,Security.authenticated(),"APPLY"):
            jo = 1
        if explicit_right(c,Security.authenticated(),"JOIN"):
            jo = 2
        self.joining_options=[["no_joining","Only when added",jo==0],["moderated","By acceptation",jo==1],["public","Freely",jo==2]]
        self.anonymous_view = explicit_right(c,Security.anonymous(),"VIEW")
        for t in Contestant.filter(contest=c):
            if t.accepted:
                self.accepted.append([t,t.members()])
            else:
                self.pending.append([t,t.members()])
