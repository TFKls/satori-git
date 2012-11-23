# vim:ts=4:sts=4:sw=4:expandtab
import urllib
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.tables import *
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django import forms

def build_url(*args, **kwargs):
    get = kwargs.pop('get', {})
    url = reverse(*args, **kwargs)
    if get:
        url += '?' + urllib.urlencode(get)
    return url

@contest_view
def view(request, page_info):
    contest = page_info.contest
    admin = page_info.contest_is_admin 

#part two:
    submitable = [["",'Select a problem']]
    algo = [["0","C++ Check"]]
    suitetable = [["",'Select a suite']]
    problems = ProblemMapping.filter(ProblemMappingStruct(contest=contest))
    problems.sort(key=lambda p: p.code)
    for problem in problems:
        if Privilege.demand(problem, "MANAGE"):#ask gucio
            submitable.append((problem.id, problem.code+": "+problem.title))

    if request.REQUEST.get('problem', '') != '':
        problem = ProblemMapping(int(request.REQUEST.get('problem')))
        suits = TestSuite.filter(TestSuiteStruct(problem=problem.problem))
        for suite in sorted(suits, key=lambda ts: ts.name):
            suitetable.append((suite.id, suite.name))

    #    suits = TestSuite.filter(TestSuiteStruct(problem=problem))
    #    suits.sort(key=lambda p: p.code)
    #
    #    for suite in suits:
    #       suitetable.append((suite.id, suite.code+": "+suite.title))

    class ComparisonForm(forms.Form):
        refresh = forms.CharField(widget=forms.HiddenInput(), required=False)
        problem = forms.ChoiceField(submitable,label='Please select problem')
        problem.widget.attrs['onchange']='this.form.elements["refresh"].value="1"; this.form.submit();'
        algorithm = forms.ChoiceField(algo, label='Please select algorithm')
        test_suite = forms.ChoiceField(suitetable, label='Please select test suite')
        regexp = forms.CharField(max_length=64)
        
            
    if request.method == "POST":
        if request.POST.get('refresh', '') != '':
            data = dict([(str(k),str(v)) for (k,v) in request.POST.items() if k != 'refresh'])
            return HttpResponseRedirect(build_url('findcribs',args=[page_info.contest.id],get=data))

        form = ComparisonForm(request.POST,request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            problem = ProblemMapping(int(data["problem"]))
            algorithm = int(data["algorithm"])
            test_suite = TestSuite(int(data["test_suite"]))
            regexp = data["regexp"]

            Comparison.create(ComparisonStruct(problem=problem, algorithm=algorithm, test_suite=test_suite, regexp=regexp))
            return HttpResponseRedirect(reverse('results',args=[page_info.contest.id]))
    else:
        form = ComparisonForm(initial={'refresh': None, 'problem' : request.GET.get('problem',None), 'algorithm' : request.GET.get('algorithm', "0"), 'test_suite' : request.GET.get('test_suite', 0), 'regexp' : request.GET.get('regexp', '')})
    
    return render_to_response('findcribs.html',{ 'page_info' : page_info, 'resultsplus' : results, 'form' : form})
