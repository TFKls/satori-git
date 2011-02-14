from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.web.urls import PROJECT_PATH
from satori.client.common import want_import
want_import(globals(), '*')
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
        fn = PROJECT_PATH+'/simple_uzi_checker.py'
        f = open(fn)
        pd = ParamsDict(parse_judge(f.read()))
        self.form = pd.create_form()
        