from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from copy import deepcopy
from _Widget import Widget

class EditSuiteWidget(Widget):
    pathName = 'editsuite'
    def __init__(self,params,path):
        self.htmlFile='htmls/editsuite.html'
        d = follow(params,path)
        if 'id' in d.keys():
            id = int(d['id'][0])
        else:
            id = None
        if id:
            ts = TestSuite.filter({'id':id})[0]
            self.ts = ts
            problem = ts.problem
            selected = [t.id for t in ts.get_tests()]
        else:
            selected = []
            problem = Problem.filter(ProblemStruct(id=int(d['problem'][0])))[0]
        self.problem = problem
        self.back_to = ToString(params)
        self.back_path = path
        self.accumulators = Global.get_instance().get_accumulators()
        alltests = Test.filter(TestStruct(problem=problem))
        alltests.sort(key=lambda x : x.name)
        self.tests = []
        for t in alltests:
            self.tests.append([t,t.id in selected])
