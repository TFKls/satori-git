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
    results.allcontestants = sorted(Web.get_accepted_contestants(contest=contest,limit=max_limit).contestants+Web.get_contest_admins(contest=contest,limit=max_limit).contestants,key = lambda c : c.name)
    
    contestant = None                                                   # check if results are needed for the single contestant or for everyone
    try:
        contestant = Contestant(int(results.my_params['contestant']))
    except:
        pass
    
    problem = None
    try:                                                                # check if the results are needed for a single problem
        problem = ProblemMapping(int(results.my_params['problem']))
    except:
        pass
        
        
    status = results.my_params.get('status',None)                       # check if the results are filtered by status
        
    query = Web.get_results(contest=contest,contestant=contestant,problem=problem)
    
    for row in query.results:
        results.data.append({'id' : row.submit.id, 'contestant' : row.contestant.name, 'problem' : row.problem_mapping.code, 'status' : row.status,
                             'contestant_link' : results.params_subst_link({'contestant' : str(row.contestant.id) }), 
                             'problem_link' : results.params_subst_link({'problem' : str(row.problem_mapping.id)}), 
                             })
    if status:
        results.data = [r for r in results.data if r['status']==status]
        
    results.autopaginate()
    results.pagedata['nofilterlink'] = results.params_subst_link(deleted_my=['contestant','problem','status'])
    return render_to_response('results.html',{ 'page_info' : page_info, 'results' : results})



@contest_view
def placeholder(request, page_info):
    contest = page_info.contest
    admin = page_info.contest_is_admin
    class SubmitsTable(ResultTable):
       
        def length(self):
            return len(self.results)
            
        @staticmethod
        def default_limit():
            return 30
        @staticmethod
        def max_limit():
            return 100000                
                               
        def __init__(self,req,prefix=''):                                                                                                                                                     
            super(SubmitsTable,self).__init__(req=req,prefix=prefix,autosort=False)
            if admin and 'cts' in self.filters.keys():
                contestant = Contestant(int(self.filters['cts']))
            else:
                contestant = None
            if 'problem' in self.filters.keys():
                problem = ProblemMapping(int(self.filters['problem']))
            else:
                problem = None
            limit = int(self.params['limit'])
            if limit==0:
                limit = max_limit
            page = int(self.params['page'])
            self.showdiff=int(self.params.get('diff','0'))
            if self.filters.get('suite1','disable_filter')!='disable_filter':
                suite1 = TestSuite(int(self.filters['suite1']))
                if suite1.problem != problem.problem:
                    suite1 = None
            else:
                suite1 = None
            if self.filters.get('suite2','disable_filter')!='disable_filter':
                suite2 = TestSuite(int(self.filters['suite2']))
                if suite2.problem != problem.problem:
                    suite2 = None
            else:
                suite2 = None
            compsuite = admin and suite1 and suite2
            detailed_tsr = admin and self.filters.get('allsuites','0')=='1'
            query = Web.get_results(contest=contest,contestant=contestant,problem=problem,offset=(page-1)*limit,limit=limit,detailed_tsr=(detailed_tsr or compsuite))
            self.results = query.results
            self.total = query.count
            self.fields.append(TableField(name='No.',
                                          value=(lambda table,i: table.results[i].submit.id), 
                                          render=(lambda table,i: format_html(u'<a class="stdlink" href="{0}">{1}</a>', reverse('view_result',args=[contest.id,table.results[i].submit.id]), table.results[i].submit.id)),
                                          id=1))
            if self.showdiff:
                self.fields.append(TableField(name='',value='',render=(lambda table,i: format_html(u'<input type="radio" name="diff_1" value="{0}"/>', table.results[i].submit.id)),id='diff_1'))
                self.fields.append(TableField(name='',value='',render=(lambda table,i: format_html(u'<input type="radio" name="diff_2" value="{0}"/>', table.results[i].submit.id)),id='diff_2'))            
            if admin:
                cts = TableField(name='Contestant',value=(lambda table,i: table.results[i].contestant.name),
                                                  render=(lambda table,i: format_html(u'<a class="stdlink" href="{0}">{1}</a>', table.getparams(filters={'cts' : unicode(table.results[i].contestant.id)},page=1), table.results[i].contestant.name)),
                                                            id='cts')
                
                choices = [[unicode(c.id),c.name] for c in Web.get_accepted_contestants(contest=contest,limit=self.max_limit()).contestants]
                self.fields.append(cts)
                self.filter_functions.append(FilterFunction(name='Contestant',prefix='cts',choices=choices))
            prf = TableField(name='Problem',value=(lambda table,i: table.results[i].problem_mapping.code), id='problem')
            pmlist = Web.get_problem_mapping_list(contest=contest)
            pmlist.sort(key=lambda p: p.problem_mapping.code)
            pchoices = [[unicode(p.problem_mapping.id),p.problem_mapping.code+' ('+p.problem_mapping.title+')'] for p in pmlist]
            self.fields.append(prf)
            self.filter_functions.append(FilterFunction(name='Problem',prefix='problem',choices=pchoices))
            if admin and problem:
                schoices = [ [unicode(s.id),s.name] for s in TestSuite.filter(TestSuiteStruct(problem=problem.problem))]
                self.filter_functions.append(FilterFunction(name='Compare suite',prefix='suite1',choices=schoices))                
                self.filter_functions.append(FilterFunction(name='with suite',prefix='suite2',choices=schoices))                
            self.fields.append(TableField(name='Time',value=(lambda table,i: table.results[i].submit.time), id=4))
            def statusfunction(suite):
                def suitestatus(table,i):
                    for k in table.results[i].test_suite_results:
                        if k.test_suite==suite:
                            kst = k.test_suite_result.status
                            return format_html('<div class="submitstatus"><div class="sta{0}">{1}</div></div>', kst, kst)
                return suitestatus
            def different(table,i):
                if statusfunction(suite1)(table,i)==statusfunction(suite2)(table,i): 
                    return 'Matching' 
                else: 
                    return 'Different'
            def different_render(table,i):
                if statusfunction(suite1)(table,i)==statusfunction(suite2)(table,i): 
                    return mark_safe('<span class="highlight_pos">Matching</span>')
                else: 
                    return mark_safe('<span class="highlight_neg">Different</span>')
            
            if not compsuite:
                self.fields.append(TableField(name='Status',value=(lambda table,i: table.results[i].status),
                                          render=(lambda table,i: format_html('<div class="submitstatus"><div class="sta{0}">{1}</div></div>', table.results[i].status, table.results[i].status)),
                                          id=5,css='status'))
            else:
                self.fields.append(TableField(name=suite1.name,value='',
                                          render=statusfunction(suite1)
                                          ,id=6,css='status'))
                self.fields.append(TableField(name=suite2.name,value='',
                                          render=statusfunction(suite2)
                                          ,id=7,css='status'))
                suitediff = TableField(name='Different',value=different, render=different_render,id='suitediff',css=['description','centered'])
                self.fields.append(suitediff)
                self.add_autofilter(suitediff)
            def suite_results(table,i):
                r = table.results[i]
                return '<br/>'.join([tsr.test_suite.name+': '+tsr.test_suite_result.status for tsr in r.test_suite_results])
            if detailed_tsr and not compsuite:
                self.fields.append(TableField(name='Results',value='',render=suite_results,id=6))
            if self.showdiff:
                newdiff = 0
            else:
                newdiff = 1
            self.difflink = self.getparams(diff=newdiff)
            if admin and not compsuite:
                self.filter_functions.append(FilterFunction(prefix='allsuites',name='Show results on',choices=[('0','Default suite'),('1','All suites')],default='0',showall=False))
    results = SubmitsTable(req = request.GET,prefix='results')
    return render_to_response('results.html',{ 'page_info' : page_info, 'results' : results })
