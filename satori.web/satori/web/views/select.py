# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from satori.web.utils.forms import AlertList
from satori.web.utils.generic_table import GenericTable
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


class CreateContestForm(forms.Form):
    name = forms.CharField(required=True, label="Name")
    description = forms.CharField(required=False, label="Description")
    

@general_view
def view(request, page_info):
    create_form = None
    alerts = AlertList()
    can_create = Privilege.global_demand('MANAGE_CONTESTS')
    show_archived = request.GET.get('show_archived',None)=='on'
    if request.method=="POST":
        if can_create and "addcontest" in request.POST.keys():
            create_form = CreateContestForm(request.POST)
            if create_form.is_valid():
                data = create_form.cleaned_data
                try:
                    contest = Contest.create(ContestStruct(name=data['name'],description=data['description']))
                    return HttpResponseRedirect(reverse('contest_manage',args=[contest.id]))
                except:
                    alerts.add('Contest creation failed!','danger')
                    create_form = CreateContestForm()
    if can_create and not create_form:
        create_form = CreateContestForm()
    
    participating = GenericTable('participating',request.GET)
    other = GenericTable('other',request.GET)
    for table in [participating,other]:
        if table.my_params.get('archived','0')=='1':
            table.show_archived = 1
        else:
            table.show_archived = 0
        table.archived_link = table.params_subst_link(subst_my = {'archived' : str(1-table.show_archived)})
    
    for contest_info in Web.get_contest_list():
        row = {'name' : contest_info.contest.name, 'id' : contest_info.contest.id, 'description' : contest_info.contest.description, 'archived' : contest_info.contest.archived}
        if contest_info.is_admin:
            row['status'] = 'admin'
            participating.data.append(row)
        elif contest_info.contestant:
            if contest_info.contestant.accepted:
                row['status'] = 'contestant'
            else:
                row['status'] = 'pending'
            participating.data.append(row)
        else:
            if contest_info.can_join:
                row['status'] = 'join'
            elif contest_info.can_apply:
                row['status'] = 'apply'
            else:
                row['status'] = None
            other.data.append(row)
        participating.default_sortfield = 'name'
        participating.autosort()
        participating.autopaginate()
        other.default_sortfield = 'name'
        other.autosort()
        other.autopaginate()
        
    return render_to_response('select_contest.html', {'page_info' : page_info, 'participating' : participating, 'other' : other, 'create_form' : create_form, 'alerts' : alerts})
