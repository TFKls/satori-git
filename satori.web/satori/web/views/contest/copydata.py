# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.forms import StatusBar
from satori.web.utils.tables import *
from django import forms
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

@contest_view
def copyproblems(request,page_info):
    contest = page_info.contest
    class CopyTable(ResultTable):
        def __init__(self,req=request.GET,prefix='pcopy'):
            super(CopyTable,self).__init__(req,prefix)
            try:
                source = Contest.filter(ContestStruct(id=int(self.filters['contest'])))[0]
            except:
                source = None
            if source:
                self.results = ProblemMapping.filter(ProblemMappingStruct(contest=source))
            self.fields.append(TableField(id='check',name='Code',sortable=True,value=lambda table,i : table.results[i].code,render=(lambda table,i : format_html(u'<input type="checkbox" name="mid_{0}">{1}', table.results[i].id, table.results[i].code))))
            self.fields.append(TableField(id='title',name='Title',value=(lambda table,i : table.results[i].title)))
            self.fields.append(TableField(id='based',name='Based on',value=(lambda table,i : table.results[i].problem.name+' ('+table.results[i].problem.description+')')))
            self.fields.append(TableField(id='ascode',name='Target code',sortable=False,value=(lambda table,i : format_html('<input class="transparent_box" type="text" size="8" name="code_{0}"/>', table.results[i].id))))
            self.fields.append(TableField(id='stm',name='Copy statement?',sortable=False,render=(lambda table,i : format_html('<input type="checkbox" name="stm_{0}"/>', table.results[i].id))))
            
            self.filter_functions.append(FilterFunction(name='Contest',prefix='contest',showall=False,choices=[[-1,'Select']] + [[c.contest.id,c.contest.name] for c in Web.get_contest_list() if c.is_admin ],default=-1))
    copytable = CopyTable()
    if request.method=="POST":
        source = Contest(int(request.POST["cid"]))
        for k in request.POST.keys():
            if k[:4]=='mid_':
                pm = ProblemMapping(int(k[4:]))
                if 'stm_'+k[4:] in request.POST.keys():
                    statement = pm.statement
                else:
                    statement = None
                code = request.POST.get('code_'+k[4:],'')
                if code=='':
                    code = pm.code
                npm = ProblemMapping.create(ProblemMappingStruct(contest=contest,code=code,problem=pm.problem,title=pm.title,default_test_suite=pm.default_test_suite))
                npm.statement_files_set_map(pm.statement_files_get_map())
                npm.statement = statement
        return HttpResponseRedirect(reverse('contest_problems',args=[contest.id]))
    return render_to_response('copy_problems.html', {'page_info' : page_info, 'copytable' : copytable} )
            
@contest_view
def view(request, page_info):
    contest = page_info.contest
    if not request.GET.has_key('preid'):
    
        class PreForm(forms.Form):
            preid = forms.ChoiceField(choices=[(c.contest.id,c.contest.name) for c in Web.get_contest_list() if c.is_admin],required=True,label='Copy from contest')
        preform = PreForm()
        return render_to_response('contest_copy.html', {'page_info' : page_info, 'preform' : preform})
    source = Contest(int(request.GET['preid']))
    class CopyForm(forms.Form):
        problem = forms.ChoiceField(choices=[[p.problem_mapping.id,p.problem_mapping.title] for p in Web.get_problem_mapping_list(contest=source)],label='Copy single problem')
        code = forms.CharField(required=False, label='with code')
        
    class MassForm(forms.Form):
        problems = forms.BooleanField(required=False, label='Copy all problems')
        accepted = forms.BooleanField(required=False, label='Copy all accepted users')
        pending = forms.BooleanField(required=False, label='Copy all pending users')
    copyform = CopyForm()
    massform = MassForm()
    bar = StatusBar()
    if request.method=="POST":
        if 'copyone' in request.POST.keys():
            copyform = CopyForm(request.POST)
            if copyform.is_valid():
                data = copyform.cleaned_data
                oldmapping = ProblemMapping(int(data['problem']))
                code = data['code']
                try:
                    newmapping = ProblemMapping.create(ProblemMappingStruct(contest=contest,problem=oldmapping.problem,code=code,title=oldmapping.title,default_test_suite=oldmapping.default_test_suite,statement=oldmapping.statement))
                    newmapping.statement_files_set_map(oldmapping.statement_files_get_map())
                    return HttpResponseRedirect(reverse('contest_problems',args=[contest.id]))
                except:
                    bar.errors.append('Copy failed!')
        if 'masscopy' in request.POST.keys():
            massform = MassForm(request.POST)
            if massform.is_valid():
                data = massform.cleaned_data
                if data['problems']:
                    ok = True
                    for i in  Web.get_problem_mapping_list(contest=source):
                        oldmapping = i.problem_mapping
                        newmapping = None
                        try:
                            newmapping = ProblemMapping.create(ProblemMappingStruct(contest=contest,problem=oldmapping.problem,code=oldmapping.code,title=oldmapping.title,default_test_suite=oldmapping.default_test_suite))
                            newmapping.statement_files_set_map(oldmapping.statement_files_get_map())
                            newmapping.statement = oldmapping.statement
                        except:
                            if newmapping:
                                newmapping.delete()
                            bar.errors.append('Copy of problem '+oldmapping.code+' ('+oldmapping.title+') failed!')
                            ok = False
                    if ok:
                        bar.messages.append('All problems copied');
                if data['accepted']:
                    ok = True
                    for c in Web.get_accepted_contestants(contest=source,limit=100000,offset=0).contestants:
                        try:
                            Contestant.create(ContestantStruct(name=c.name,contest=contest,accepted=True,invisible=c.invisible,login=c.login),c.get_member_users())
                        except:
                            bar.errors.append('Copy of user '+c.name+' failed!')
                            ok = False
                    if ok:
                        bar.messages.append('All accepted users copied.');
                if data['pending']:
                    ok = True
                    for c in Web.get_pending_contestants(contest=source,limit=100000,offset=0).contestants:
                        try:
                            Contestant.create(ContestantStruct(name=c.name,contest=contest,accepted=False,invisible=c.invisible,login=c.login),c.get_member_users())
                        except:
                            bar.errors.append('Copy of user '+c.name+' failed!')
                            ok = False
                    if ok:
                        bar.messages.append('All accepted users copied.');
                        
    return render_to_response('contest_copy.html', {'page_info' : page_info, 'copyform' : copyform, 'massform' : massform, 'status_bar' : bar})
#    if request.method == "POST":
