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
