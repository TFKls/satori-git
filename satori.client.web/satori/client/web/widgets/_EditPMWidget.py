from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common import want_import
want_import(globals(), '*')
from _Widget import Widget

class EditPMWidget(Widget):
    pathName = 'editprmap'
    def __init__(self,params,path):
        self.htmlFile='htmls/editprmap.html'
        d = follow(params,path)
        id = int(d['problemid'][0])
        pm = ProblemMapping.filter({'id':id})[0]
        p = pm.problem
        self.pm = pm
        self.problem = p
        self.tests = Test.filter(TestStruct(problem=p))
        self.suites = TestSuite.filter(TestSuiteStruct(problem=p))
        self.back_to = ToString(params)
        self.path = path
        s = pm.statement_get_str('text')
        if s:
            self.statement = s
        self.dts = pm.default_test_suite
