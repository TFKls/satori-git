from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

class EditPMWidget(Widget):
    pathName = 'editprmap'
    def __init__(self,params,path):
        self.htmlFile='htmls/editprmap.html'
        d = follow(params,path)
        id = int(d['problemid'][0])
        p = ProblemMapping.filter({'id':id})[0]
        self.pm = p
        self.problem = p.problem
        self.tests = list()
        self.back_to = ToString(params)
        self.path = path
        self.statement = p.statement_get_str('text')
        dts = p.default_test_suite
        for t in Test.filter({'problem':p.problem}):
            checked = bool(TestMapping.filter({'test':t, 'suite':dts}))
            self.tests.append([t,checked])
