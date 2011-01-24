from satori.client.web.queries import *
from satori.client.web.URLDictionary import *
from _Widget import Widget

class ViewSubmitWidget(Widget):
    pathName = 'viewsubmit'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/viewsubmit.html'
        d = follow(params,path)
        c = ActiveContest(params)
        s = Submit.filter({'id' : int(d['id'][0])})[0]
        res = s.get_result()
        self.sid = s.id
        self.user = res.contestant
        self.problem = res.problem
        self.time = s.time
        self.details = res.details
        self.status = res.status
#        tsr = TestSuiteResult.filter(TestSuiteResultStruct(submit=s,test_suite = s.problem.default_test_suite))
#        if tsr:
#            tsr = tsr[0]
#            self.results = []
        self.isadmin = Allowed(c,'MANAGE')
        if self.isadmin:
            self.suites = TestSuiteResult.filter(TestSuiteResultStruct(submit=s))
            self.results = []
            for t in Test.filter(TestStruct(problem=s.problem.problem)):
                testres = TestResult.filter(TestResultStruct(test=t,submit=s))
                if len(testres)>0:
                    testres = testres[0]
                    d = {}
                    d['test'] = t
                    d['attr'] = []
                    oa = OaMap(testres.oa_get_map())
                    for k,v in oa.get_map().items():
                        if not v.is_blob:
                            d['attr'].append([k,v.value])
                    self.results.append(d)                        
#        else:
#            self.results = None
            self.results.sort(key=lambda r: r['test'].name)
        rawcode = s.data_get_blob('content').read(100000)
        self.code = text2html('::\n\n'+''.join('  '+s for s in rawcode.splitlines(True)))
#        self.content = text2html(s.content)
