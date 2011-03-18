# vim:ts=4:sts=4:sw=4:expandtab
import glob
import os
import tempfile
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.files import valid_attachments
from satori.web.utils.shortcuts import fill_image_links
from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

class ContestNewsEditForm(forms.Form):
    name = forms.CharField(label="Message title")
    content = forms.CharField(required=False,widget=forms.Textarea, label="Content")
    fid = forms.CharField(required=True, widget=forms.HiddenInput) # (temporary) folder id
    is_sticky = forms.BooleanField(label="Always at the top", required=False)
    is_public = forms.BooleanField(label="Show to all visitors", required=False)

@contest_view
def view(request, page_info):
    messages = Web.get_subpage_list_for_contest(page_info.contest,True)
    for m in messages:
        m.html = fill_image_links(m.html, 'Subpage', m.subpage.id, 'content_files')
    messages.sort(key=lambda m : [m.subpage.is_sticky, m.subpage.date_created], reverse=True)
    return render_to_response('news.html',{'page_info' : page_info, 'messages' : messages })

@contest_view
def add(request, page_info):
    if request.method=="POST":
        form = ContestNewsEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            fid = data['fid']
            message = Subpage.create_for_contest(SubpageStruct(is_announcement=True,
                                                               contest=page_info.contest,
                                                               name=data['name'],
                                                               content='',
                                                               is_sticky=data['is_sticky'],
                                                               is_public=data['is_public']))
            Privilege.grant(Security.anonymous(),message,'VIEW')
            for ufile in glob.glob(os.path.join(fid, '*')):
                message.content_files_set_blob_path(os.path.basename(ufile), ufile)
            try:
                message.content = data['content']
            except SphinxException as sphinxException:
                return render_to_response('news_add.html', { 'form' : form,
                                                             'fid' : fid,
                                                             'page_info' : page_info,
                                                             'sphinxException' : sphinxException })
            return HttpResponseRedirect(reverse('contest_news',args=[page_info.contest.id]))
    else:
        #TODO(kalq): Create a hash instead of full pathname
        fid = tempfile.mkdtemp()
        form = ContestNewsEditForm(initial={ 'fid' : tempfile.mkdtemp() })
    return render_to_response('news_add.html', { 'page_info' : page_info, 
                                                 'fid' : fid,
                                                 'form' : form })

@contest_view
def edit(request, page_info,id):
    message = Subpage.filter(SubpageStruct(id=int(id)))[0]
    if request.method=="POST":
        form = ContestNewsEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            fid = data['fid']
            for rfile in request.POST:
                if rfile.startswith('rfile'):
                    message.content_files_delete(request.POST[rfile])
            for ufile in glob.glob(os.path.join(fid, '*')):
                message.content_files_set_blob_path(os.path.basename(ufile), ufile)
            try:
                message.modify(SubpageStruct(name=data['name'],
                                             content=data['content'],
                                             is_sticky=['is_sticky'],
                                             is_public=data['is_public']))
            except SphinxException as sphinxException:
                attachments = valid_attachments(message.content_files_get_list())
                return render_to_response('news_edit.html', { 'attachments' : attachments,
                                                              'fid' : fid,
                                                              'form' : form,
                                                              'message' : message, 
                                                              'page_info' : page_info,
                                                              'sphinxException' : sphinxException })
            return HttpResponseRedirect(reverse('contest_news',args=[page_info.contest.id]))
    else:
        fid = tempfile.mkdtemp()
        form = ContestNewsEditForm(initial={ 'name' : message.name,
                                             'content' : message.content,
                                             'fid' : fid,
                                             'is_public' : message.is_public,
                                             'is_sticky' : message.is_sticky})
    attachments = valid_attachments(message.content_files_get_list())
    return render_to_response('news_edit.html', { 'attachments' : attachments,
                                                  'fid' : fid,
                                                  'form' : form,
                                                  'message' : message,
                                                  'page_info' : page_info })

@contest_view
def delete(request, page_info,id):
    messages = []
    for message in Subpage.get_for_contest(page_info.contest,True):
        messages.append([message,text2html(message.content)])
    return render_to_response('news.html',{'page_info' : page_info, 'messages' : messages })
