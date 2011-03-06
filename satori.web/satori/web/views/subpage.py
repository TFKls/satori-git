# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from satori.web.utils.shortcuts import fill_image_links
from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

class GlobalSubpageEditForm(forms.Form):
    name = forms.CharField(label="Subpage name")
    content = forms.CharField(required=False,widget=forms.Textarea, label="Content")
    is_public = forms.BooleanField(label="Show in every contest", required=False)

@general_view
def view(request, page_info,id):
    sinfo = Web.get_subpage_info(Subpage(int(id)))
    name = sinfo.subpage.name
    content = fill_image_links(sinfo.html, 'Subpage', id, 'content_files')
    can_edit = sinfo.is_admin
    return render_to_response('subpage.html',{'page_info' : page_info, 'subpage' : sinfo.subpage, 'content' : content, 'can_edit' : can_edit})

@general_view
def create(request, page_info):
    if request.method=="POST":
        form = GlobalSubpageEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            subpage = Subpage.create_global(SubpageStruct(is_announcement=False,name=data["name"],content=data["content"]))
            return HttpResponseRedirect(reverse('subpage',args=[subpage.id]))
    else:
        form = GlobalSubpageEditForm()
    return render_to_response('subpage_create.html',{'page_info' : page_info, 'form' : form})

@general_view
def edit(request, page_info,id):
    subpage = Subpage.filter(SubpageStruct(id=int(id)))[0]
    if request.method=="POST":
        form = GlobalSubpageEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            subpage.modify(SubpageStruct(name=data["name"],content=data["content"],is_public=data["is_public"]))
            return HttpResponseRedirect(reverse('subpage',args=[subpage.id]))
    else:
        form = GlobalSubpageEditForm(initial={'name' : subpage.name, 'content' : subpage.content, 'is_public' : subpage.is_public})
    return render_to_response('subpage_edit.html',{'page_info' : page_info, 'form' : form, 'subpage' : subpage})

