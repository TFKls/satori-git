# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from django import forms
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from satori.web.utils.forms import SatoriDateTimeField,RenderObjectButton
from satori.web.utils.tables import *

@contest_view
def view(request, page_info):
    contest = page_info.contest
    is_admin = page_info.contest_is_admin
    all_contestants = Web.get_accepted_contestants(contest=contest,offset=0,limit=100000).contestants
    all_problems = [p.problem_mapping for p in Web.get_problem_mapping_list(contest=contest)]
    all_problems.sort(key=lambda p : p.code)
    class ExtendForm(forms.Form):
        contestant_choices = [[str(p.id), p.name] for p in all_contestants]
        problem_choices = [['all','All problems']]+[[p.id, p.code+': '+p.title] for p in all_problems]
        contestant = forms.ChoiceField(choices=contestant_choices,required=True)
        problem = forms.ChoiceField(choices=problem_choices,required=True)
        start = SatoriDateTimeField(required=False)
        finish = SatoriDateTimeField(required=False)

    class ExtendTable(ResultTable):
        def default_limit(self):
            return 20
        def __init__(self,req,prefix=''):
            super(ExtendTable,self).__init__(req=req,prefix=prefix,default_sort=2,default_desc=True)
            privs = {}
            for m in all_problems:
                k = Privilege.list(entity=m,right='SUBMIT')
                for r,t in Privilege.list(entity=m,right='SUBMIT').items():
                    if t.start_on:
                        start = str(t.start_on)
                    else:
                        start = '-infty'
                    if t.finish_on:
                        finish = str(t.finish_on)
                    else:
                        finish = 'infty'
                    times = start+'/'+finish
                    try:
                        c = Contestant(r.id)
                        n = c.name
                        if not privs.has_key(c):
                            privs[c] = {}
                        if not privs[c].has_key(times):
                            privs[c][times] = m.code
                        else:
                            privs[c][times] += ','+m.code
                    except:
                        pass
            self.results = []
            for c,key in privs.items():
                s = ""
                for times,codes in key.items():
                    if s!="":
                        s+=", "
                    s += codes+': '+times
                self.results.append([c,s])
            self.total = len(self.results)
            self.fields.append(TableField(name='Contestant',value=(lambda table,i : table.results[i][0].name),id=1))
            self.fields.append(TableField(name='Status',value=(lambda table,i : table.results[i][1]),id=2))
            self.fields.append(TableField(name='',value='Revoke',render=(lambda table,i : RenderObjectButton(name='revoke',buttonname='Revoke',id=table.results[i][0].id,css='button button_small')),id=3))
        
    if request.method == "POST":
        if 'revoke' in request.POST.keys():
            c = Contestant(int(request.POST['id']))
            for p in all_problems:
                Privilege.revoke(role=c,entity=p,right='SUBMIT')
            return HttpResponseRedirect(reverse('extends',args=[page_info.contest.id]))
        form = ExtendForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            c = Contestant(int(data['contestant']))
            start_on = data.get('start',None)
            finish_on = data.get('finish',None)
            if data['problem']=='all':
                for p in all_problems:
                    Privilege.grant(role=c,entity=p,right='SUBMIT',times=PrivilegeTimes(start_on=start_on,finish_on=finish_on))
            else:
                p = ProblemMapping(int(data['problem']))
                Privilege.grant(role=c,entity=p,right='SUBMIT',times=PrivilegeTimes(start_on=start_on,finish_on=finish_on))
            return HttpResponseRedirect(reverse('extends',args=[page_info.contest.id]))
    else:
        form = ExtendForm()
    extends = ExtendTable(req=request.GET,prefix='extend')
    return render_to_response('extends.html', {'page_info' : page_info, 'form' : form, 'extends' : extends})

        