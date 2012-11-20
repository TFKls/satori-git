# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.tables import *
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django import forms

@contest_view
def view(request, page_info):
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
                                          render=(lambda table,i: '<a class="stdlink" href="'+reverse('view_result',args=[contest.id,table.results[i].submit.id])+'">'
                                                                    +unicode(table.results[i].submit.id)+'</a>'),
                                          id=1))
            if self.showdiff:
                self.fields.append(TableField(name='',value='',render=(lambda table,i: '<input type="radio" name="diff_1" value="'+unicode(table.results[i].submit.id)+'"/>'),id='diff_1'))
                self.fields.append(TableField(name='',value='',render=(lambda table,i: '<input type="radio" name="diff_2" value="'+unicode(table.results[i].submit.id)+'"/>'),id='diff_2'))          
            if admin:
                cts = TableField(name='Contestant',value=(lambda table,i: table.results[i].contestant.name),
                                                  render=(lambda table,i: '<a class="stdlink" href="'+table.getparams(filters={'cts' : unicode(table.results[i].contestant.id)},page=1)+'">'+table.results[i].contestant.name+'</a>'),
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
                            return '<div class="submitstatus"><div class="sta'+kst+'">'+kst+'</div></div>'
                return suitestatus
            def different(table,i):
                if statusfunction(suite1)(table,i)==statusfunction(suite2)(table,i): 
                    return 'Matching' 
                else: 
                    return 'Different'
            def different_render(table,i):
                if statusfunction(suite1)(table,i)==statusfunction(suite2)(table,i): 
                    return '<span class="highlight_pos">Matching</span>' 
                else: 
                    return '<span class="highlight_neg">Different</span>'
            
            if not compsuite:
                self.fields.append(TableField(name='Status',value=(lambda table,i: table.results[i].status),
                                          render=(lambda table,i: '<div class="submitstatus"><div class="sta'+unicode(table.results[i].status)+'">'+unicode(table.results[i].status)+'</div></div>')
                                          ,id=5,css='status'))
#radiobuttonscribs
                self.fields.append(TableField(name='',value='',render=(lambda table,i: '<input type="radio" name="crib_1" value="'+unicode(table.results[i].submit.id)+'"/>'),id='crib_1'))
                self.fields.append(TableField(name='',value='',render=(lambda table,i: '<input type="radio" name="crib_2" value="'+unicode(table.results[i].submit.id)+'"/>'),id='crib_2'))
            else:
                self.fields.append(TableField(name=suite1.name,value='',
                                          render=statusfunction(suite1)
                                          ,id=6,css='status'))
                self.fields.append(TableField(name=suite2.name,value='',
                                          render=statusfunction(suite2)
                                          ,id=7,css='status'))
                suitediff = TableField(name='Different',value=different, render=different_render,id='suitediff',css=['description','centered'])
                self.fields.append(suitediff)
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
    return render_to_response('findcribs.html',{ 'page_info' : page_info, 'resultsplus' : results })
