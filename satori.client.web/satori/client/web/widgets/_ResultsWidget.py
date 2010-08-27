from copy import deepcopy
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common import *
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
        self.submits = []
        for o in Submit.filter(): # TODO: correct 
            if o.owner.contest==c:
                s = {}
                id = str(o.id)
                s["id"] = id
                s["time"] = o.time
                s["user"] = o.owner.user.fullname
                s["problem"] = o.problem.code
                s["status"] = o.shortstatus
                s["details"] = o.longstatus
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
