from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from datetime import datetime
from operator import attrgetter,itemgetter
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
            entry = {}
            entry['code'] = p.code
            if p.statement:
                entry['showlink'] = GetLink(DefaultLayout(dict = params,maincontent = 'showpm',problemid = [str(p.id)]),'')
            try:
                entry['pdf'] = p.oa_get_blob_hash('pdfstatement')
            except:
                pass
            entry['editlink'] = GetLink(DefaultLayout(dict = params,maincontent = 'editprmap',problemid = [str(p.id)]),'')
            published = False
            stime = None
            ftime = None
            privs = Privilege.filter({'role' : r, 'object' : p, 'right' : 'SUBMIT'})
            for priv in privs:
                if ((not priv.startOn) or priv.startOn>datetime.now()) and ((not priv.finishOn) or priv.endOn<datetime.now()):
                    published = True
                stime = str(priv.startOn)
                ftime = str(priv.finishOn)
            if published:
                stime = 'Published'
            entry['stime'] = stime
            entry['ftime'] = ftime
            entry['p'] = p
            self.problems.append(entry)
        self.problems.sort(key=itemgetter('code'))
        self.potential = Problem.filter()
        self.back_to = ToString(params)
        self.back_path = path
