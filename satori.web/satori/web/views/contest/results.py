# coding=utf-8
# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.tables import *
from satori.web.utils.generic_table import GenericTable
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django import forms

@contest_view
def view(request, page_info):
    contest = page_info.contest
    admin = page_info.contest_is_admin
    results = GenericTable('results',request.GET)
    max_limit = 50000
    results.pagedata = {}
    results.problems = sorted(Web.get_problem_mapping_list(contest=contest), key=lambda p: p.problem_mapping.code)
    if admin:
        results.allcontestants = sorted(Web.get_accepted_contestants(contest=contest,limit=max_limit).contestants+Web.get_contest_admins(contest=contest,limit=max_limit).contestants,key = lambda c : c.name)
    
    try:
        contestant = Contestant(int(results.my_params['contestant']))
    except:
        contestant = None                                                   # check if results are needed for the single contestant or for everyone
    
    try:                                                                # check if the results are needed for a single problem
        problem = ProblemMapping(int(results.my_params['problem']))
    except:
        problem = None
        
        
    results.status_filter = results.my_params.get('status',"")                       # check if the results are filtered by status
    
    detailed_tsr = None
    results.suite_show = None
    results.enable_cmp = bool(results.my_params.get('enable_cmp',None))
    results.suite_cmp = None
    results.only_diff = bool(results.my_params.get('only_diff',None))
    
    if problem and admin:                                               # a long fragment about suite comparing
        try:
            results.suite_show = TestSuite(int(results.my_params['suite_show']))        # shall we show result on another than default suite?
        except:
            pass
        try:
            if results.enable_cmp:
                results.suite_cmp = TestSuite(int(results.my_params['suite_cmp']))      # shall we take another suite for comparison?
        except:
            pass
            
        detailed_tsr = admin and (results.suite_show or results.suite_cmp)                                   # shall we ask for all suite results?
        results.suites = TestSuite.filter(TestSuiteStruct(problem=problem.problem))
    
    query = Web.get_results(contest=contest,contestant=contestant,problem=problem,limit=max_limit,offset=0,detailed_tsr=detailed_tsr)
    
    for row in query.results:
        status = row.status                                     # find the right suite result, if other than default
        if results.suite_show:
            for tsr in row.test_suite_results:
                if tsr.test_suite==results.suite_show:
                    status = tsr.test_suite_result.status
            
        status_cmp = row.status                                 # the same for comparison suite
        if results.suite_cmp:
            for tsr in row.test_suite_results:
                if tsr.test_suite==results.suite_cmp:
                    status_cmp = tsr.test_suite_result.status
        
        generic_status = "Waiting"
        
        if not status:                                          # something to show before checking master sets the "QUE" status
            status = generic_status
        if not status_cmp:
            status_cmp = generic_status
            
        results.data.append({'id' : row.submit.id, 'contestant' : row.contestant.name, 'problem' : row.problem_mapping.code + u' – ' + row.problem_mapping.title, 
                             'time' : row.submit.time, 'status' : status, 'status_cmp' : status_cmp, 'matching' : status==status_cmp,
                             'contestant_link' : results.params_subst_link({'contestant' : str(row.contestant.id) }), 
                             'problem_link' : results.params_subst_link({'problem' : str(row.problem_mapping.id)}), 
                             })
    if results.status_filter:
        results.data = [r for r in results.data if r['status']==results.status_filter]
    if results.only_diff:
        results.data = [r for r in results.data if r['status']!=r['status_cmp']]
        
    results.autopaginate()
    results.pagedata['nofilterlink'] = results.params_subst_link(deleted_my=['contestant','problem','status','enable_cmp','suite_show','suite_cmp','only_diff'])
    return render_to_response('results.html',{ 'page_info' : page_info, 'results' : results})


