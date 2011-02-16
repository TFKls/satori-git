# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.shortcuts import text2html
from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

class ContestSubpageEditForm(forms.Form):
    name = forms.CharField(label="Subpage name")
    content = forms.CharField(required=False,widget=forms.Textarea, label="Content")
    is_public = forms.BooleanField(label="Show to all visitors", required=False)

@contest_view
def view(request, general_page_overview,id):
    subpage = Subpage.filter(SubpageStruct(id=int(id)))[0]
    name = subpage.name
    content = subpage.content
    can_edit = Privilege.demand(subpage,'MANAGE')
    return render_to_response('subpage.html',{'general_page_overview' : general_page_overview, 'name' : name, 'content' : content, 'can_edit' : can_edit})

@contest_view
def create(request, general_page_overview):
    if request.method=="POST":
        form = ContestSubpageEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            subpage = Subpage.create_for_contest(SubpageStruct(is_announcement=False,contest=general_page_overview.contest,name=data["name"],content=data["content"]))
            return HttpResponseRedirect(reverse('contest_subpage',args=[general_page_overview.contest.id, subpage.id]))
    else:
        form = ContestSubpageEditForm()
    return render_to_response('subpage_create.html',{'general_page_overview' : general_page_overview, 'form' : form})

@contest_view
def edit(request, general_page_overview,id):
    subpage = Subpage.filter(SubpageStruct(id=int(id)))[0]
    if request.method=="POST":
        form = ContestSubpageEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            subpage.modify(SubpageStruct(name=data["name"],content=data["content"],is_public=data["is_public"]))
            return HttpResponseRedirect(reverse('contest_subpage',args=[general_page_overview.contest.id, subpage.id]))
    else:
        form = ContestSubpageEditForm({'name' : subpage.name, 'content' : subpage.content, 'is_public' : subpage.is_public})
    return render_to_response('subpage_edit.html',{'general_page_overview' : general_page_overview, 'form' : form, 'subpage' : subpage})

@contest_view
def delete(request, general_page_overview,id):
    subpage = Subpage.filter(SubpageStruct(id=int(id)))[0]
    name = subpage.name
    content = subpage.content
    return render_to_response('subpage.html',{'general_page_overview' : general_page_overview, 'name' : name, 'content' : content})
# vim:ts=4:sts=4:sw=4:expandtab


