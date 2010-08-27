from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

class ProblemsWidget(Widget):
    pathName = 'problems'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/problems.html'
        c = ActiveContest(params)
        self.problems = list()
        for p in ProblemMapping.filter({'contest':c}):
            editlink = GetLink(DefaultLayout(dict = params,maincontent = 'editprmap',problemid = [str(p.id)]),'')
            self.problems.append([p,editlink])
