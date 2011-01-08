# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget
from copy import deepcopy

class ManageUsersWidget(Widget):
    pathName = 'manusers'
    def __init__(self, params, path):
        d = follow(params,path)
        _params = deepcopy(params)
        _d = follow(_params,path)
        
        limit = 20
        
        self.htmlFile = 'htmls/manusers.html'
        c = ActiveContest(params)
        self.contest = c
        self.accepted = list()
        self.pending = list()
        
        if 'apage' in d.keys():
            apage = int(d['apage'][0])-1
        else:
            apage = 0
            
        self.apage = apage+1
        self.aoffset = apage*limit
        allacc = c.get_contestants(limit,self.aoffset)
        i = self.aoffset+1
        for contestant in allacc.contestants:
            q = {}
            q['number'] = i
            i = i+1
            q['c'] = contestant.contestant
            q['name'] = contestant.name
            q['members'] = contestant.members
            if contestant.admin:
                q['admin'] = 'Admin'
            self.accepted.append(q)
            
        self.apcount = (allacc.count+limit-1)/limit
        
        self.alinks = []
        for i in range(1,self.apcount+1):
            _d['apage'] = [str(i)]
            self.alinks.append(GetLink(_params,''))
            
        if apage>=1:
            self.ablink = self.alinks[apage-1]
        else:
            self.ablink = None
        if apage<self.apcount-1:
            self.aflink = self.alinks[apage+1]
        else:
            self.aflink = None
            
        if 'ppage' in d.keys():
            ppage = int(d['ppage'][0])-1
        else:
            ppage = 0
            
        self.ppage = ppage+1
        self.poffset = ppage*limit
        allpend = c.get_pending_contestants(limit,self.poffset)
        i = self.poffset+1
        for contestant in allpend.contestants:
            q = {}
            q['number'] = i
            i = i+1
            q['c'] = contestant.contestant
            q['name'] = contestant.name
            q['members'] = contestant.members
            self.pending.append(q)
            
        self.ppcount = (allacc.count+limit-1)/limit
        
        self.plinks = []
        for i in range(1,self.ppcount+1):
            _d['ppage'] = [str(i)]
            self.plinks.append(GetLink(_params,''))
            
        if ppage>=1:
            self.pblink = self.plinks[ppage-1]
        else:
            self.pblink = None
        if ppage<self.ppcount-1:
            self.pflink = self.plinks[ppage+1]
        else:
            self.pflink = None
            
