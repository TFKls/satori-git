# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.forms import StatusBar
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms
from satori.web.utils.shortcuts import text2html
from satori.web.utils.tables import ResultTable,TableField,format_html
from difflib import HtmlDiff,Differ
from cgi import escape

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
    if res.report:
        widget["details"] = text2html(res.report)
    widget["status"] = res.status
    widget["isadmin"] = admin
    if res.test_suite_results:
        widget["suites"] = [ {'result' : tsr.test_suite_result, 'report' : text2html(tsr.test_suite_result.report), 'attrs' : tsr.attributes, 'default' : tsr.test_suite_result.test_suite==res.problem_mapping.default_test_suite } for tsr in res.test_suite_results ]
#    if widget["suites"]:
#        widget["suites"].sort(key=lambda r: r.test_suite.name)
    class TestResultTable(ResultTable):
        @staticmethod
        def default_limit():
            return 0
        def __init__(self,req,prefix=''):
            super(TestResultTable,self).__init__(req=req,prefix=prefix,default_sort='name')
            self.results = res.test_results
            attributes = set()
            for t in self.results:
                for a in t.attributes.keys():
                    attributes.add(t.attributes[a].name)
            self.fields.append(TableField(name='Test name',value=lambda table,i : table.results[i].test.name,id='name'))
            def attribute_value(table,i,a):
                r = table.results[i]
                if a in r.attributes.keys():
                    v = r.attributes[a]
                    if v.is_blob:
                        return v.filename
                    else:
                        return v.value
                else:
                    return ''
            def attribute_render(table,i,a):
                r = table.results[i]
                if a in r.attributes.keys():
                    v = r.attributes[a]
                    if v.is_blob:
                        return format_html(u'<a class="stdlink" href="{0}">{1}</a>', reverse('download',args=['download','TestResult',unicode(r.test_result.id),a,v.filename]), v.filename)
                    else:
                        return v.value
                else:
                    return ''
            def lar(att):
                return lambda table,i : attribute_render(table,i,att)
            def lav(att):
                return lambda table,i : attribute_value(table,i,att)            
            for a in attributes:
                self.fields.append(TableField(name=a,value=lav(a),render=lar(a),id=a))
    
    if admin:
        tests = TestResultTable(req=request.GET)
    else:
        tests = None
    fullname = res.data_filename.rsplit('.',2)
    if len(fullname)==2:
        extension = '.'+fullname[1]
    else:
        extension = ''
    filename = id+extension
    rawcode = res.data
    if rawcode and rawcode!="":
        widget["code"] = text2html(u'::\n\n'+''.join(u'  '+s for s in rawcode.splitlines(True)))
    return render_to_response('viewresult.html',{'page_info' : page_info, 'widget' : widget, 'tests' : tests,'filename' : filename})


@contest_view
def diff(request, page_info):
    try:
        id0 = request.GET['diff_1']
        id1 = request.GET['diff_2']
        submit0 = Web.get_result_details(submit=Submit(int(id0)))
        submit1 = Web.get_result_details(submit=Submit(int(id1)))
        submits = [submit0,submit1]
    except:
        return HttpResponseRedirect(reverse('results',args=[unicode(page_info.contest.id)]))
    bar = StatusBar()
    codes = []
    ok = True
    for i in [0,1]:
        codes.append(submits[i].data)
        if codes[i]==None or codes[i]=="":
            ok = False
            bar.errors.append('Could not render submit '+unicode(submits[i].submit.id)+'!')
    diff_html = ""
    if ok:
        d = Differ()
        for line in d.compare(codes[1].splitlines(True),codes[0].splitlines(True)):
            if line[0]=='?':
                continue
            css = 'highlight_back'
            if line[0]=='+':
                css = 'highlight_pos'
            if line[0]=='-':
                css = 'highlight_neg'
            diff_html += '<span class="'+css+'">'+escape(line)+'</span>'
    return render_to_response('viewdiff.html',{'page_info' : page_info, 'submits' : submits, 'diff' : diff_html, 'status_bar' : bar})
        
@contest_view
def override(request, page_info, id):
    submit = Submit(int(id))
    contest = page_info.contest
    res = Web.get_result_details(submit=submit)
    report = text2html(res.report)

    if request.method=='POST' and 'rejudge' in request.POST.keys():
        submit.rejudge_test_results()
        return HttpResponseRedirect(reverse('view_result',args=[contest.id,id]))
        
    if request.method=='POST' and 'revert' in request.POST.keys():
        submit.override({})
        return HttpResponseRedirect(reverse('view_result',args=[contest.id,id]))
        
    class OverrideForm(forms.Form):
        status = forms.CharField(required=True,label='New status')
        comment = forms.CharField(required=False,widget=forms.Textarea,label='Comment')
        
    if request.method=='POST':
        form = OverrideForm(data=request.POST)
        if form.is_valid():
            status = form.cleaned_data['status']
            comment = form.cleaned_data['comment']
            m = OaMap()
            m.set_str('status',status)
            m.set_str('override_comment',comment)
            submit.override(m.get_map())
            return HttpResponseRedirect(reverse('view_result',args=[contest.id,submit.id]))
    else:
        form = OverrideForm(initial={'status' : res.status, 'comment' : '(override by '+page_info.user.name+', original status: '+res.status+')'})
    fullname = res.data_filename.rsplit('.',2)
    if len(fullname)==2:
        extension = '.'+fullname[1]
    else:
        extension = ''
    filename = id+extension
    rawcode = res.data
    if rawcode and rawcode!="":
        code = text2html(u'::\n\n'+''.join(u'  '+s for s in rawcode.splitlines(True)))
    else:
        code = None
    return render_to_response('result_override.html',{'page_info' : page_info, 'form' : form, 'submit' : res, 'filename': filename, 'code' : code, 'report' : report})
    
