# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.shortcuts import text2html
from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response


class ContestNewsEditForm(forms.Form):
    name = forms.CharField(label="Message title")
    content = forms.CharField(required=False,widget=forms.Textarea, label="Content")
#    is_sticky = forms.BoolField(description="Always at the top")
    is_public = forms.BooleanField(label="Show to all visitors", required=False)

@contest_view
def view(request, general_page_overview):
    messages = []
    for message in Subpage.get_for_contest(general_page_overview.contest,True):
        messages.append([message,text2html(message.content)])
    messages.sort(key=lambda m : m[0].date_created,reverse=True)
    return render_to_response('news.html',{'general_page_overview' : general_page_overview, 'messages' : messages })

@contest_view
def create(request, general_page_overview):
    if request.method=="POST":
        form = ContestNewsEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            Subpage.create_for_contest(SubpageStruct(is_announcement=True,contest=general_page_overview.contest,name=data["name"],content=data["content"]))
            return HttpResponseRedirect(reverse('contest_news',args=[general_page_overview.contest.id]))
    else:
        form = ContestNewsEditForm()
    return render_to_response('news_create.html',{'general_page_overview' : general_page_overview, 'form' : form})

@contest_view
def edit(request, general_page_overview,id):
    message = Subpage.filter(SubpageStruct(id=int(id)))[0]
    if request.method=="POST":
        form = ContestNewsEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            message.modify(SubpageStruct(name=data["name"],content=data["content"],is_public=data["is_public"]))
            return HttpResponseRedirect(reverse('contest_news',args=[general_page_overview.contest.id]))
    else:
        form = ContestNewsEditForm({'name' : message.name, 'content' : message.content, 'is_public' : message.is_public})
    return render_to_response('news_edit.html',{'general_page_overview' : general_page_overview, 'form' : form, 'message' : message})

@contest_view
def delete(request, general_page_overview,id):
    messages = []
    for message in Subpage.get_for_contest(general_page_overview.contest,True):
        messages.append([message,text2html(message.content)])
    return render_to_response('news.html',{'general_page_overview' : general_page_overview, 'messages' : messages })
