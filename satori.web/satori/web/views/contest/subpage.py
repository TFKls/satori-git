# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.shortcuts import fill_image_links
from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

class ContestSubpageEditForm(forms.Form):
    name = forms.CharField(label="Subpage name")
    content = forms.CharField(required=False,widget=forms.Textarea, label="Content")
    is_public = forms.BooleanField(label="Show to all visitors", required=False)

@contest_view
def view(request, page_info,id):
    sinfo = Web.get_subpage_info(Subpage(int(id)))
    content = fill_image_links(sinfo.html, 'Subpage', id, 'content_files')
    can_edit = sinfo.subpage.contest and sinfo.is_admin
    return render_to_response('subpage.html',{'page_info' : page_info, 'subpage' : sinfo.subpage, 'content' : content, 'can_edit' : can_edit})

@contest_view
def create(request, page_info):
    if request.method=="POST":
        form = ContestSubpageEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            subpage = Subpage.create_for_contest(SubpageStruct(is_announcement=False,contest=page_info.contest,name=data["name"],content=data["content"]))
            return HttpResponseRedirect(reverse('contest_subpage',args=[page_info.contest.id, subpage.id]))
    else:
        form = ContestSubpageEditForm()
    return render_to_response('subpage_create.html',{'page_info' : page_info, 'form' : form})

@contest_view
def edit(request, page_info,id):
    subpage = Subpage.filter(SubpageStruct(id=int(id)))[0]
    if request.method=="POST":
        form = ContestSubpageEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            subpage.modify(SubpageStruct(name=data["name"],content=data["content"],is_public=data["is_public"]))
            return HttpResponseRedirect(reverse('contest_subpage',args=[page_info.contest.id, subpage.id]))
    else:
        form = ContestSubpageEditForm(initial={'name' : subpage.name, 'content' : subpage.content, 'is_public' : subpage.is_public})
    return render_to_response('subpage_edit.html',{'page_info' : page_info, 'form' : form, 'subpage' : subpage})

