from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common import *
from satori.client.web.widgets import Widget

class SubmitWidget(Widget):
    pathName = 'submit'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/submit.html'
        self.back_to = ToString(params)
        c = ActiveContest(params)
        self.problems = []
        self.cid = CurrentContestant(params).id
        for p in ProblemMapping.filter(contest=c):
            if Allowed(p,'submit'):
                self.problems.append(p)
