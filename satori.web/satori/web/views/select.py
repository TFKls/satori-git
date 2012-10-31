# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from satori.web.utils.tables import *
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.html import mark_safe
from django import forms


@general_view
def apply(request, page_info, id):
    contest = Contest(int(id))
    contest.join()
    return HttpResponseRedirect(reverse('select_contest'))


class CreateForm(forms.Form):
    name = forms.CharField(required=True)
    description = forms.CharField(required=False)
    

@general_view
def view(request, page_info):
    create_form = None
    can_create = Privilege.global_demand('MANAGE_CONTESTS')
    show_archived = request.GET.get('show_archived',None)=='on'
    if request.method=="POST":
        if can_create and "addcontest" in request.POST.keys():
            create_form = CreateForm(request.POST)
            if create_form.is_valid():
                data = create_form.cleaned_data
                try:
                    contest = Contest.create(ContestStruct(name=data['name'],description=data['description']))
                    return HttpResponseRedirect(reverse('contest_manage',args=[contest.id]))
                except:
                    create_form._errors['name'] = ['Creation failed']
    if can_create and not create_form:
        create_form = CreateForm()
    
    class ContestTable(ResultTable):
        def length(self):
            return len(self.contests)
            
        @staticmethod
        def default_limit():
            return 0
            
        def __init__(self,req,prefix='',contest_list=[],operations=False):
            super(ContestTable,self).__init__(req=req,prefix=prefix,autosort=True)
            self.contests=contest_list
            self.total = len(self.contests)
            self.fields.append(TableField(name='Name',value=(lambda table,i: table.contests[i].contest.name),
                                                      render=(lambda table,i: format_html(u'<a class="stdlink" href="{0}">{1}</a>', reverse('contest_main',args=[table.contests[i].contest.id]), table.contests[i].contest.name)),
                                                      id=1 ))
            self.fields.append(TableField(name='Description',value=(lambda table,i: table.contests[i].contest.description), css='description', id=2 ))
            def button(table,i):
                s=''
                if table.contests[i].contestant and not table.contests[i].contestant.accepted:
                    s=mark_safe('<span class="signature">Pending</span>')
                if table.contests[i].contestant or table.contests[i].is_admin:
                    return s
                if table.contests[i].can_apply:
                    s = 'Apply'
                if table.contests[i].can_join:
                    s = 'Join'
                if s!='':
                    s = format_html(u'<a class="button button_small" href="{0}">{1}</a>', reverse('apply',args=[table.contests[i].contest.id]), s)
                return s
                
            self.fields.append(TableField(name='',value=(lambda table,i: ''),
                                                  render=button,id=3))
            self.filter_functions.append(FilterFunction(name='Show archived', prefix='archived', choices=[ ['0','No'], ['1','Yes'] ],check=(lambda table,i,v: v=='1' or not table.contests[i].contest.archived),default='0',showall=False))
                
    ml = []
    pl = []
    ol = []
            
    for contest_info in Web.get_contest_list():
        if contest_info.is_admin:
            ml.append(contest_info)
        elif contest_info.contestant:
            pl.append(contest_info)
        else:
            ol.append(contest_info)
    if ml:
        managed = ContestTable(req=request.GET,prefix='managed',contest_list=ml,operations=False)
    else:
        managed = None
    if pl:
        participating = ContestTable(req=request.GET,prefix='participating',contest_list=pl,operations=False)
    else:
        participating = None
    if ol:  
        other = ContestTable(req=request.GET,prefix='other',contest_list=ol,operations=True)
    else:
        other = None
    
    return render_to_response('select_contest.html', {'page_info' : page_info, 'managed' : managed, 'participating' : participating, 'other' : other, 'create_form' : create_form, 'show_archived' : show_archived})
