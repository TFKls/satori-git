from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from datetime import datetime
from _Widget import Widget

class ProblemsWidget(Widget):
    pathName = 'problems'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/problems.html'
        c = ActiveContest(params)
        r = c.contestant_role
        self.contest = c
        self.manage = c.demand_right("MANAGE")
        self.problems = list()
        for p in ProblemMapping.filter({'contest':c}):
            editlink = GetLink(DefaultLayout(dict = params,maincontent = 'editprmap',problemid = [str(p.id)]),'')
            published = False
            stime = None
            ftime = None
            privs = Privilege.filter({'role' : r, 'object' : p, 'right' : 'SUBMIT'})
            for priv in privs:
                if (not priv.startOn or priv.startOn>datetime.now()) and (not prov.finishOn or priv.endOn<datetime.now()):
                    published = True
                stime = str(priv.startOn)
                ftime = str(priv.finishOn)
            if published:
                self.stime = 'Published'
            self.problems.append([p,editlink,stime,ftime])
        self.potential = Problem.filter()
        self.back_to = ToString(params)
        self.back_path = path
