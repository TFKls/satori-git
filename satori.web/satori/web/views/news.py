# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from satori.web.utils.shortcuts import text2html, fill_image_links
from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response


class NewsEditForm(forms.Form):
    name = forms.CharField(label="Message title")
    content = forms.CharField(required=False,widget=forms.Textarea, label="Content")
#    is_sticky = forms.BoolField(description="Always at the top")
#    is_public = forms.BooleanField(label="Show to all visitors", required=False)

@general_view
def view(request, page_info):
    messages = Web.get_subpage_list_global(True)
    for m in messages:
        m.html = fill_image_links(m.html, 'Subpage', m.subpage.id, 'content_files')
    messages.sort(key=lambda m : m.subpage.date_created, reverse=True)
    return render_to_response('news.html',{'page_info' : page_info, 'messages' : messages })

@general_view
def add(request, page_info):
    if request.method=="POST":
        form = NewsEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            message = Subpage.create_global(SubpageStruct(is_announcement=True,contest=page_info.contest,name=data["name"],content=data["content"]))
            Privilege.grant(Security.anonymous(),message,'VIEW')
            return HttpResponseRedirect(reverse('news'))
    else:
        form = NewsEditForm()
    return render_to_response('news_create.html',{'page_info' : page_info, 'form' : form})

@general_view
def edit(request, page_info,id):
    message = Subpage.filter(SubpageStruct(id=int(id)))[0]
    if request.method=="POST":
        form = NewsEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            message.modify(SubpageStruct(name=data["name"],content=data["content"]))
            return HttpResponseRedirect(reverse('news'))
    else:
        form = NewsEditForm({'name' : message.name, 'content' : message.content, 'is_public' : message.is_public})
    return render_to_response('news_edit.html',{'page_info' : page_info, 'form' : form, 'message' : message})

@general_view
def delete(request, page_info,id):
    messages = []
    for message in Subpage.get_for_contest(page_info.contest,True):
        messages.append([message,text2html(message.content)])
    return render_to_response('news.html',{'page_info' : page_info, 'messages' : messages })
