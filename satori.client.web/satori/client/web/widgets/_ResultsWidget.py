# vim:ts=4:sts=4:sw=4:expandtab
from copy import deepcopy
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

# results table (a possible main content)
class ResultsWidget(Widget):
    pathName = 'results'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/results.html'
        c = ActiveContest(params)
        _params = deepcopy(params)
        _params2 = deepcopy(params)
        d = follow(_params,path)
        d2 = follow(_params2,path)
        
        if not ('shown' in d.keys()):
            shown = []
        else:
            shown = d['shown']
        if 'user' in d.keys():
            curuser = d['user'][0]
        else:
            curuser = ''
        self.isadmin = Privilege.demand(c,"MANAGE")
        self.back_to = ToString(params)
        self.back_path = path

        limit = 20

        if 'page' in d.keys():
            page = int(d['page'][0])-1
        else:
            page = 0
            
        self.page = page+1
        self.offset = page*limit

        cct = CurrentContestant(params)
        
        if self.isadmin:
            if curuser == 'mine':
                submits = c.get_results(contestant=cct,limit=limit,offset=self.offset)
            elif curuser.isdigit():
                submits = c.get_results(contestant=Contestant(int(curuser)),limit=limit,offset=self.offset)
            else:
                submits = c.get_all_results(limit=limit,offset=self.offset)
#            self.users = [('', 'All', False), ('mine', 'Your own', False)] + [(c.id, c.name, False) for c in Contestant.filter(ContestantStruct(contest=c))]
        else:
            submits = c.get_results(contestant=cct,limit=limit,offset=self.offset)

        self.pcount = (submits.count+limit-1)/limit
        self.displaypages = self.pcount>1
        
        self.links = []
        for i in range(1,self.pcount+1):
            d2['page'] = [str(i)]
            self.links.append(GetLink(_params2,''))
            
        if page>=1:
            self.blink = self.links[page-1]
        else:
            self.blink = None
        if page<self.pcount-1:
            self.flink = self.links[page+1]
        else:
            self.flink = None
        self.submits = [] 
        for submit in submits.results:
            s = {}
            id = str(submit.submit.id)
            s["id"] = id
            s["time"] = submit.submit.time.strftime("%b %d, %Y, %H:%M:%S")
            s["user"] = submit.contestant
            s["problem"] = submit.problem
            s["status"] = submit.status
            s["details"] = submit.details
            s["viewlink"] = GetLink(DefaultLayout(dict=params,maincontent='viewsubmit',id=[str(id)],contest=c),'')
            _shown = deepcopy(shown)
            if id in _shown:
                s["showdetails"] = True
                _shown.remove(id)
            else:
                s["showdetails"] = False
                _shown.append(id)
            _shown.sort()
            d['shown'] = _shown
            if _shown == []:
                del d['shown']
            s["link"] = GetLink(_params,'')
            self.submits.append(s)

