# vim:ts=4:sts=4:sw=4:expandtab
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.shortcuts import text2html
from django import forms
from django.shortcuts import render_to_response


class NewsEditForm(forms.Form):
    name = forms.CharField()
    content = forms.CharField(required=False,widget=forms.Textarea)

@contest_view
def view(request, general_page_overview):
    messages = []
    for message in Subpage.get_for_contest(general_page_overview.contest,True):
        messages.append([message,text2html(message.content)])
    return render_to_response('news.html',{'general_page_overview' : general_page_overview, 'messages' : messages })

@contest_view
def create(request, general_page_overview):
    if request.method=="POST":
        form = NewsEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            Subpage.create_for_contest(SubpageStruct(name=data["name"],content=data["content"]))
            return HttpResponseRedirect(url
    else:
        form = NewsEditForm()
    return render_to_response('newsadd.html',{'general_page_overview' : general_page_overview, 'form' : form})

@contest_view
def edit(request, general_page_overview,id):
    message = Subpage.filter(SubpageStruct(id=int(id)))[0]
    if request.method=="POST":
        form = NewsEditForm(request.POST)
    else:
        form = NewsEditForm({'name' : message.name, 'content' : message.content})
    return render_to_response('newsedit.html',{'general_page_overview' : general_page_overview, 'form' : form })

@contest_view
def delete(request, general_page_overview,id):
    messages = []
    for message in Subpage.get_for_contest(general_page_overview.contest,True):
        messages.append([message,text2html(message.content)])
    return render_to_response('news.html',{'general_page_overview' : general_page_overview, 'messages' : messages })
