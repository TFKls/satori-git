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
        self.manage = Privilege.demand(c,"MANAGE")
        self.problems = list()
        for p in ProblemMapping.filter({'contest':c}):
            statement = p.statement_get_str('text')
            entry = {}
            entry['code'] = p.code
            if statement:
                entry['showlink'] = GetLink(DefaultLayout(dict = params,maincontent = 'showpm',problemid = [str(p.id)]),'')
            try:
                entry['pdf'] = p.statement_get_blob_hash('pdf')
            except:
                pass
            if Allowed(p,'MANAGE'):
                entry['editlink'] = GetLink(DefaultLayout(dict = params,maincontent = 'editprmap',problemid = [str(p.id)]),'')
                entry["visible"] = "No"
                times = Privilege.get(r, p, 'SUBMIT')
                if times:
                    if ((times.start_on is None) or (times.start_on < datetime.now())) and ((times.finish_on is None) or (times.finish_on > datetime.now())):
                        entry["from"] = "Active"
                        if times.start_on:
                            entry["from"] = entry["from"]+" from "+times.start_on
                    if times.start_on and times.start_on > datetime.now():
                        entry["from"] = "Start on "+times.start_on
                    if times.finish_on:
                        if times.finish_on>datetime_now():
                            entry["until"] = "Finish on "+times.finish_on
                        else:
                            entry["until"] = "Submits ended "+times.finish_on
                    else:
                        entry["until"] = "Submitable forever"
                    if (times.start_on is None) or (times.start_on < datetime.now()):
                        entry["visible"] = "Yes"
                else:
                    entry["from"] = "No dates set"
                view = Privilege.get(r, p, 'VIEW')
                if view:
                    if ((view.start_on is None) or (view.start_on < datetime.now())) and ((view.finish_on is None) or (view.finish_on > datetime.now())):
                        entry["visible"] = "Yes"
            entry['p'] = p
            self.problems.append(entry)
        self.problems.sort(key=itemgetter('code'))
        self.potential = Problem.filter()
        self.back_to = ToString(params)
        self.back_path = path
