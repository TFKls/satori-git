from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

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
        try:
            cjudge = p.default_test_data_get_blob("judge")
            self.judgehash = p.default_test_data_get_blob_hash("judge")
        except:
            cjudge = None
        try:
            cjudge = t.oa_get_blob("judge")
            self.judgehash = t_oa_get_blob("judge")
        except:
            pass
        self.back_to = ToString(params)
        self.back_path = path
        if cjudge:
            reader = cjudge
            judge_content = reader.read(reader.length)
            reader.close()
            self.judge = parse_judge(judge_content)
            for d in self.judge:
                cv = p.default_test_data_get(d["name"])
                if t:
                    cv = t.oa_get(d["name"])
                if not cv and d["default"]:
                    cv = {'value' : d["default"]}
                if cv:
                    d["cv"] = cv["value"]
