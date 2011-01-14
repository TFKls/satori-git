from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

class SubmitWidget(Widget):
    pathName = 'submit'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/submit.html'
        self.back_to = ToString(params)
        c = ActiveContest(params)
        self.problems = []
        self.cid = CurrentContestant(params).id
        for p in ProblemMapping.filter({'contest':c}):
            if Allowed(p,'SUBMIT'):
                self.problems.append(p)
        self.problems.sort(key=lambda p : p.code)
        if len(self.problems)==0:
            self.noproblem = True
            