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
        d = follow(_params,path)
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

        if self.isadmin:
            if curuser == 'mine':
                submits = c.get_results(CurrentContestant(d))
            elif curuser.isdigit():
                submits = c.get_results(Contestant.filter({id:int(curuser)})[0])
            else:
                submits = c.get_all_results()
            self.users = [('', 'All', False), ('mine', 'Your own', False)] + [(c.id, c.name, False) for c in Contestant.filter(ContestantStruct(contest=c))]
        else:
            submits = c.get_results(CurrentContestant(d))

        self.submits = [] 
        for submit in submits.results:
            s = {}
            id = str(submit.submit.id)
            s["id"] = id
            s["time"] = submit.submit.time
            s["user"] = submit.contestant
            s["problem"] = submit.problem
            s["status"] = submit.status
            s["details"] = submit.details
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
