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

class ShowCribs:
    def __init__(self, problem, regexp, submit_1, submit_2, user_1, user_2, result):
        self.problem=problem
        self.regexp=regexp
        self.submit_1=submit_1
        self.submit_2=submit_2
        self.user_1=user_1
        self.user_2=user_2
        self.result=result

@contest_view
def view(request, page_info):
    contest = page_info.contest
    admin = page_info.contest_is_admin 
    results = []

    submitable = [["",'Select a comparison']]
    boundtable = [["10",'10'], ["20",'20'],["30",'30'],["40",'40']]

    problems = ProblemMapping.filter(ProblemMappingStruct(contest=contest))
    problems.sort(key=lambda p: p.code)
    for problem in problems:
        if Privilege.demand(problem, "MANAGE"):
            comparisons = Comparison.filter(ComparisonStruct(problem_mapping=problem))
            comparisons.sort(key=lambda p: p.creation_date)
            for comp in comparisons:
                submitable.append((comp.id, str(comp.problem_mapping.code) +": "+str(comp.execution_date)))

    if request.REQUEST.get('comparison', '') != '':
        comparison = Comparison(int(request.REQUEST.get('comparison'))) 
       # bound = 10
       # if isinstance( bound, int ):
        bound = int(request.REQUEST.get('bound'))
   
        compresults = ComparisonResult.filter(ComparisonResultStruct(comparison = comparison))
        for cres in sorted(compresults, key=lambda ts: ts.result):
            if bound <= 0:
                break
            bound -= 1
            results.append(ShowCribs(problem = str(comparison.problem_mapping.code), regexp = cres.comparison.regexp, submit_1 = str(cres.submit_1.id),  user_1 = cres.submit_1.contestant.usernames, submit_2 = str(cres.submit_2.id), user_2 = cres.submit_2.contestant.usernames, result = str(cres.result)))

    class ComparisonForm(forms.Form):
        refresh = forms.CharField(widget=forms.HiddenInput(), required=False)
        comparison = forms.ChoiceField(submitable,label='Please select comparison')
        comparison.widget.attrs['onchange']='this.form.elements["refresh"].value="1"; this.form.submit();'
        bound = forms.ChoiceField(boundtable, label = 'Please select number')
        bound.widget.attrs['onchange']='this.form.elements["refresh"].value="1"; this.form.submit();'
            
    if request.method == "POST":
        if request.POST.get('refresh', '') != '':
            data = dict([(str(k),str(v)) for (k,v) in request.POST.items() if k != 'refresh'])
            return HttpResponseRedirect(build_url('cribsresults',args=[page_info.contest.id],get=data))

        form = ComparisonForm(request.POST,request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            comparison = ProblemMapping(int(data["comparison"]))
            bound = data["bound"]

            return HttpResponseRedirect(reverse('cribsresults',args=[page_info.contest.id]))
    else:
        form = ComparisonForm(initial={'refresh': None, 'comparison' : request.GET.get('comparison',None), 'bound' : request.GET.get('bound', '')})
    
    return render_to_response('cribsresults.html',{ 'page_info' : page_info, 'form' : form, 'results' : results})
