# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from satori.web.utils.shortcuts import text2html

@contest_view
def view(request, page_info, id):
    submit = Submit(int(id))
    contest = page_info.contest
    res = Web.get_result_details(submit=submit)
    admin =  page_info.contest_is_admin
    widget = {}
    widget["sid"] = submit.id
    widget["contestant"] = res.contestant
    widget["problem"] = res.problem_mapping
    widget["time"] = submit.time
    widget["details"] = text2html(res.report)
    widget["status"] = res.status
    widget["isadmin"] = admin
    widget["suites"] = res.test_suite_results
    if widget["suites"]:
        widget["suites"].sort(key=lambda r: r.test_suite.name)
    widget["results"] = res.test_results
    if widget["results"]:
        widget["results"].sort(key=lambda r: r.test.name)
    fullname = res.data_filename.rsplit('.',2)
    if len(fullname)==2:
        extension = '.'+fullname[1]
    else:
        extension = ''
    filename = id+extension
    rawcode = res.data
    if rawcode and rawcode!="":
        widget["code"] = text2html(u'::\n\n'+''.join(u'  '+s for s in rawcode.splitlines(True)))
    return render_to_response('viewresult.html',{'page_info' : page_info, 'widget' : widget, 'filename' : filename})


@contest_view
def override(request, page_info, id):
    submit = Submit(int(id))
    contest = page_info.contest
    submit.rejudge_test_results()
    return HttpResponseRedirect(reverse('view_result',args=[contest.id,id]))