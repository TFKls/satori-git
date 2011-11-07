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
                problem = Problem(int(self.filters['problem']))
            else:
                problem = None
            limit = int(self.params['limit'])
            if limit==0:
                limit = max_limit
            page = int(self.params['page'])
            query = Web.get_results(contest=contest,contestant=contestant,problem=problem,offset=(page-1)*limit,limit=limit)
            self.results = query.results
            self.total = query.count
            self.fields.append(TableField(name='No.',
                                          value=(lambda table,i: table.results[i].submit.id), 
                                          render=(lambda table,i: '<a class="stdlink" href="'+reverse('view_result',args=[contest.id,table.results[i].submit.id])+'">'
                                                                    +unicode(table.results[i].submit.id)+'</a>'),
                                          id=1))
            
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
            self.fields.append(TableField(name='Time',value=(lambda table,i: table.results[i].submit.time), id=4))
            self.fields.append(TableField(name='Status',value=(lambda table,i: table.results[i].status),
                                          render=(lambda table,i: '<div class="submitstatus"><div class="sta'+unicode(table.results[i].status)+'">'+unicode(table.results[i].status)+'</div></div>')
                                          ,id=5,css='status'))
    
    results = SubmitsTable(req = request.GET,prefix='results')
    return render_to_response('results.html',{ 'page_info' : page_info, 'results' : results })
