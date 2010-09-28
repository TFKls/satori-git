from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

class EditProblemWidget(Widget):
    pathName = 'editproblem'
    def __init__(self,params,path):
        self.htmlFile='htmls/editproblem.html'
        d = follow(params,path)
        id = int(d['problemid'][0])
        p = Problem.filter({'id':id})[0]
        self.p = p
        self.judges = Global.get_instance().checkers_get_list()
        self.judgehash = p.default_test_data_get_blob_hash("judge")
        try:
            cjudge = p.default_test_data_get_blob("judge")
        except:
            cjudge = None
        self.back_to = ToString(params)
        self.back_path = path
        if cjudge:
            reader = cjudge
            judge_content = reader.read(reader.length)
            reader.close()
            self.judge = parse_judge(judge_content)
            for d in self.judge:
                if d["type"]=="value":
                    cv = p.default_test_data_get_str(d["name"])
                else:
                    cv = p.default_test_data_get_blob_hash(d["name"])
                if not cv and d["default"]:
                    cv = d["default"]
                if cv:
                    d["cv"] = cv
        self.tests = []
        for t in Test.filter({'problem' : p}):
            link = ToString(DefaultLayout(maincontent='edittest',dict=params,testid=[str(t.id)],action=['edit']))
            self.tests.append([t,link])
        self.addlink = ToString(DefaultLayout(maincontent='edittest',dict=params,problemid=[str(p.id)],action=['add']))
