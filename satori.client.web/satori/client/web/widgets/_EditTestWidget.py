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
