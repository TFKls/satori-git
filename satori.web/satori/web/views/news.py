# vim:ts=4:sts=4:sw=4:expandtab
import glob
import os
import tempfile
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from satori.web.utils.files import valid_attachments
from satori.web.utils.shortcuts import text2html, fill_image_links, render_to_json
from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

class NewsEditForm(forms.Form):
    name = forms.CharField(label="Message title")
    fid = forms.CharField(required=True, widget=forms.HiddenInput) # (temporary) folder id
    content = forms.CharField(widget=forms.Textarea, label="Content")
    is_sticky = forms.BooleanField(label="Always at the top", required=False)
    is_public = forms.BooleanField(label="Show in every contest", required=False)

@general_view
def view(request, page_info):
    messages = Web.get_subpage_list_global(True)
    for m in messages:
        #TODO(kalq): Check this - subpage looks strange here
        #TODO(kalq): Add attachments here
        m.html = fill_image_links(unicode(m.html), 'Subpage', m.subpage.id, 'content_files')
    messages.sort(key=lambda m : [m.subpage.is_sticky, m.subpage.date_created], reverse=True)
    return render_to_response('news.html', { 'page_info' : page_info, 
                                             'messages' : messages })

@general_view
def add(request, page_info):
    if request.method=="POST":
        form = NewsEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            fid = data['fid']
            message = Subpage.create_global(SubpageStruct(is_announcement=True,
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
                message.delete()
                return render_to_response('news_add.html', { 'form' : form,
                                                             'fid' : fid,
                                                             'page_info' : page_info,
                                                             'sphinxException' : sphinxException })
            except e:
                message.delete()
                raise e
            return HttpResponseRedirect(reverse('news'))
        else:
            #TODO(kalq): Find out why sometimes valid forms land here.
            fid = form.data['fid'] if 'fid' in form.data else tempfile.mkdtemp()
    else:
        #TODO(kalq): Create a hash instead of full pathname
        fid = tempfile.mkdtemp()
        form = NewsEditForm(initial={ 'fid' : tempfile.mkdtemp() })
    return render_to_response('news_add.html', { 'page_info' : page_info, 
                                                 'fid' : fid,
                                                 'form' : form })

@general_view
def edit(request, page_info,id):
    message = Subpage.filter(SubpageStruct(id=int(id)))[0]
    if request.method=="POST":
        if 'delete' in request.POST.keys():
            message.delete()
            return HttpResponseRedirect(reverse('news'))
        form = NewsEditForm(request.POST)
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
            return HttpResponseRedirect(reverse('news'))
    else:
        fid = tempfile.mkdtemp()
        form = NewsEditForm(initial={ 'name' : message.name,
                                      'content' : message.content,
                                      'fid' : tempfile.mkdtemp(),
                                      'is_public' : message.is_public,
                                      'is_sticky' : message.is_sticky})
    attachments = valid_attachments(message.content_files_get_list())
    return render_to_response('news_edit.html', { 'attachments' : attachments,
                                                  'fid' : fid,
                                                  'form' : form,
                                                  'message' : message,
                                                  'page_info' : page_info })

@general_view
def delete(request, page_info,id):
    messages = []
    for message in Subpage.get_for_contest(page_info.contest,True):
        messages.append([message,text2html(message.content)])
    return render_to_response('news.html',{'page_info' : page_info, 'messages' : messages })
