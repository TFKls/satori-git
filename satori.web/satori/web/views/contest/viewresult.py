# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from django.shortcuts import render_to_response
from satori.web.utils.shortcuts import text2html

@general_view
def view(request, general_page_overview, contestid, id):
    submit = Submit.filter(SubmitStruct(id=int(id)))[0]
    contest = general_page_overview.contest
    res = submit.get_result()
    admin =  general_page_overview.contest_is_admin
    widget = {}
    widget["sid"] = submit.id
    widget["contestant"] = res.contestant
    widget["problem"] = res.problem
    widget["time"] = submit.time
    widget["details"] = res.details
    widget["status"] = res.status
    widget["isadmin"] = admin
    if admin:
        widget["suites"] = TestSuiteResult.filter(TestSuiteResultStruct(submit=s))
        widget["results"] = []
        for test in Test.filter(TestStruct(problem=submit.problem.problem)):
            testres = TestResult.filter(TestResultStruct(test=test,submit=submit))
            if len(testres)>0:
                testres = testres[0]
                d = {}
                d['test'] = test
                d['attr'] = []
                oa = OaMap(testres.oa_get_map())
                for k,v in oa.get_map().items():
                    if not v.is_blob:
                        d['attr'].append([k,v.value])
                widget["results"].append(d)                        
        widget["results"].sort(key=lambda r: r['test'].name)
    rawcode = submit.data_get_blob('content').read(100000)
    rawcode = unicode(rawcode,'utf8')
    widget["code"] = text2html(u'::\n\n'+''.join(u'  '+s for s in rawcode.splitlines(True)))
    return render_to_response('viewresult.html',{'general_page_overview' : general_page_overview, 'widget' : widget})
