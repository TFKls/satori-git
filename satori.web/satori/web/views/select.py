# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django import forms

class CreateForm(forms.Form):
    name = forms.CharField(required=True)
    description = forms.CharField(required=False)

@general_view
def view(request, page_info):
    create_form = None
    can_create = Privilege.global_demand('MANAGE_CONTESTS')
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
        for id in request.POST.keys():
            contest = Contest(int(id))
            contest.join()
    if can_create and not create_form:
        create_form = CreateForm()
    managed = []
    participating = []
    other = []
    for contest_info in Web.get_contest_list():
        if contest_info.is_admin:
            managed.append(contest_info)
        elif contest_info.contestant:
            participating.append(contest_info)
        else:
            other.append(contest_info)
    return render_to_response('select_contest.html', {'page_info' : page_info, 'managed' : managed, 'participating' : participating, 'other' : other, 'create_form' : create_form})
