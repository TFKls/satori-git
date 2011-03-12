# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from django.shortcuts import render_to_response
from satori.web.utils.shortcuts import text2html

@contest_view
def view(request, page_info, id):
    submit = Submit.filter(SubmitStruct(id=int(id)))[0]
    contest = page_info.contest
    res = submit.get_result()
    admin =  page_info.contest_is_admin
    widget = {}
    widget["sid"] = submit.id
    widget["contestant"] = res.contestant
    widget["problem"] = res.problem
    widget["time"] = submit.time
    widget["details"] = text2html(res.details)
    widget["status"] = res.status
    widget["isadmin"] = admin
    if admin:
        widget["suites"] = TestSuiteResult.filter(TestSuiteResultStruct(submit=submit))
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
    reader = submit.data_get_blob('content')
    fullname = reader.filename.rsplit('.',2)
    if len(fullname)==2:
        extension = '.'+fullname[1]
    else:
        extension = ''
    filename = str(submit.id)+extension
    rawcode = reader.read(100000)
    reader.close()
    try:
        rawcode = unicode(rawcode,'utf8')
        widget["code"] = text2html(u'::\n\n'+''.join(u'  '+s for s in rawcode.splitlines(True)))
    except:
        widget["code"] = None
    return render_to_response('viewresult.html',{'page_info' : page_info, 'widget' : widget, 'filename' : filename})
