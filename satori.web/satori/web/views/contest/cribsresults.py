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
    results = ''#'<tr><td>Regexp</td></tr>'
    problems = ProblemMapping.filter(ProblemMappingStruct(contest=contest))
    problems.sort(key=lambda p: p.code)
    for problem in problems:
        comparisons = Comparison.filter(ComparisonStruct(problem_mapping=problem))
        comparisons.sort(key=lambda p: p.creation_date)
        for q in comparisons:

            results += '<tr>'
            results += '<td>Problem: ' + str(problem.code) + ' CreationDate: '+ str(q.creation_date) + ' ExecutionDate: '+ str(q.execution_date) + ' Regexp'  + q.regexp + '</td></tr>'
    
    return render_to_response('cribsresults.html',{ 'page_info' : page_info, 'resultsplus' : results}) 
