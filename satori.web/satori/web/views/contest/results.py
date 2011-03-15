# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from django.shortcuts import render_to_response
from django import forms

@contest_view
def view(request, page_info):
    max_contestants=500
    limit = 20
    contest = page_info.contest
    if not page_info.contest_is_admin:
        results=contest.get_results(contestant=page_info.contestant, limit=1000).results
        return render_to_response('results.html',{ 'page_info' : page_info, 'results' : results})
    contestants = contest.get_contestants(offset=0,limit=max_contestants).contestants
    contestant_choices = [[cinfo.contestant.id,cinfo.name] for cinfo in contestants]
    contestant_choices.append(["all","All results"])
    problems = Web.get_problem_mapping_list(contest=contest)
    problem_choices = [[pinfo.problem_mapping.id,pinfo.problem_mapping.code + ' - ' + pinfo.problem_mapping.title] for pinfo in problems]
    problem_choices.append(["all","All problems"])
    def key(c):
        if c[0]=="all":
             return None
        else:
             return c[1]
    contestant_choices.sort(key=key)
    problem_choices.sort(key=key)
    
    class ShowResultsForm(forms.Form):
        contestant = forms.ChoiceField(choices=contestant_choices, required=False)
        problem = forms.ChoiceField(choices=problem_choices, required=False)
    pars = request.GET
    form = ShowResultsForm(pars)
    pid = pars.get('problem','all')
    cid = pars.get('contestant','all')
    page = int(pars.get('page',0))
    if pid=='all':
        problem = None
    else:
        problem = Problem(int(pid))
    if cid=='all':
        results_aux = contest.get_all_results(problem=problem,limit=limit,offset=page*limit)
    else:
        results_aux = contest.get_results(problem=problem,contestant=Contestant(int(cid)),limit=limit,offset=page*limit)
    results = results_aux.results
    rescount = results_aux.count
    pagecount = (rescount+limit-1)/limit
    loop = range(0,pagecount)
    page_params = {'page' : page, 'loop' : loop, 'problem' : pid, 'contestant' : cid, 'pagecount' : pagecount }
    return render_to_response('results.html',{ 'page_info' : page_info, 'results' : results, 'form' : form, 'page_params' : page_params })
