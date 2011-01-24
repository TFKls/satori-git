from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from copy import deepcopy
from _Widget import Widget

class EditProblemWidget(Widget):
    pathName = 'editproblem'
    def __init__(self,params,path):
        self.htmlFile='htmls/editproblem.html'
        d = follow(params,path)
        id = int(d['problemid'][0])
        p = Problem.filter({'id':id})[0]
        self.p = p
        """

        jhash = Global.get_instance().checkers_get_list()[0]
        judge = 
        if cjudge:
            reader = cjudge
            judge_content = reader.read(reader.length)
            reader.close()
            self.judge = parse_judge(judge_content)
        judge = 
        self.judgehash = p.default_test_data_get_blob_hash("judge")
        try:
            cjudge = p.default_test_data_get_blob("judge")
        except:
            cjudge = None
        self.back_to = ToString(params)
        self.back_path = path
            for d in self.judge:
                if d["type"]=="value":
                    cv = p.default_test_data_get_str(d["name"])
                else:
                    cv = p.default_test_data_get_blob_hash(d["name"])
                if not cv and d["default"]:
                    cv = d["default"]
                if cv:
                    d["cv"] = cv """
                    
        self.suites = []
        for ts in TestSuite.filter(TestSuiteStruct(problem=p)):
            link = ToString(DefaultLayout(maincontent='editsuite',dict=params,id=[str(ts.id)]))
            self.suites.append([ts,link])
        self.addsuitelink = ToString(DefaultLayout(maincontent='editsuite',dict=params,problem=[str(p.id)]))
        self.tests = []
#        _params = deepcopy(params)
#        _d = follow(_params,path)
        for t in Test.filter({'problem' : p}):
            link = ToString(DefaultLayout(maincontent='edittest',dict=params,testid=[str(t.id)],action=['edit']))
            attr = t.data_get_list()
            self.tests.append([t,link,attr])
        self.tests.sort(key=lambda triple : triple[0].name)
        self.addlink = ToString(DefaultLayout(maincontent='edittest',dict=params,problemid=[str(p.id)],action=['add']))

"""
class EditTestWidget(Widget):
    pathName = 'edittest'
    def __init__(self,params,path):
        self.htmlFile='htmls/edittest.html'
        d = follow(params,path)
        t = None
        if d['action'][0]=='add':
            pid = int(d['problemid'][0])
            p = Problem.filter({'id':pid})[0]
        else:
            tid = int(d['testid'][0])
            t = Test.filter({'id':tid})[0]
            p = t.problem
        self.p = p
        self.test = t
        self.judges = Global.get_instance().checkers_get_list()
        if 'judge' in d.keys():
            jhash = d['judge'][0]
        else:
            try:
                jhash = p.default_test_data_get_blob_hash("judge")
            except:
                jhash = None
            try:
                jhash = t.data_get_blob_hash("judge")
            except:
                pass
        self.judgehash = jhash
        cjudge = None
        for j in self.judges:
            if j.value==jhash:
                cjudge = Global.get_instance().checkers_get_blob(j.name)
        self.back_to = ToString(params)
        self.back_path = path
        if cjudge:
            reader = cjudge
            judge_content = reader.read(reader.length)
            reader.close()
            self.judge = parse_judge(judge_content)
            for d in self.judge:
                cv = None
                if t:
                    try:
                        cv = t.data_get(d["name"])
                    except:
                        pass
                if not cv:
                    try:
                        cv = p.default_test_data_get(d["name"])
                    except:
                        pass
                if not cv and d["default"]:
                    cv = {'value' : d["default"]}
                if cv:
                    d["cv"] = cv["value"]
"""