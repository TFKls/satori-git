from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common import *
from satori.client.web.widgets import Widget

class RepositoryWidget(Widget):
    pathName = 'repository'
    def __init__(self,params,path):
        self.htmlFile='htmls/repository.html'
        d = follow(params,path)
        self.problems = list()
        for p in Problem.filter():
            d = DefaultLayout(dict=params, maincontent='editproblem', problemid=[str(p.id)])
            self.problems.append([p,GetLink(d,'')])
        self.back_to = ToString(params)
        self.back_path = path