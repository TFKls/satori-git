# vim:ts=4:sts=4:sw=4:expandtab
import glob
import os
import tempfile
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
from satori.web.utils.files import valid_attachments
from satori.web.utils.shortcuts import fill_image_links
from satori.web.utils.shortcuts import render_to_json, text2html
from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

class GlobalSubpageEditForm(forms.Form):
    name = forms.CharField(label="Subpage name")
    fid = forms.CharField(required=True, widget=forms.HiddenInput) # (temporary) folder id
    content = forms.CharField(required=False, widget=forms.Textarea, label="Content")
    is_public = forms.BooleanField(label="Show in every contest", required=False)
    
@general_view
def view(request, page_info,id):
    sinfo = Web.get_subpage_info(Subpage(int(id)))
    attachments = valid_attachments(sinfo.subpage.content_files_get_list())
    content = fill_image_links(unicode(sinfo.html), 'Subpage', id, 'content_files')
    can_edit = sinfo.is_admin
    return render_to_response('subpage.html', { 'attachments' : attachments,
                                                'can_edit' : can_edit,
                                                'content' : content,
                                                'page_info' : page_info, 
                                                'subpage' : sinfo.subpage })

@general_view
def add(request, page_info):
    if request.method=="POST":
        form = GlobalSubpageEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            fid = data['fid']
            subpage = Subpage.create_global(SubpageStruct(is_announcement=False,
                                                               content='',
                                                               name=data['name'],
                                                               is_public=data['is_public']))
            for ufile in glob.glob(os.path.join(fid, '*')):
                subpage.content_files_set_blob_path(os.path.basename(ufile), ufile)
            try:
                subpage.content = data["content"]
            except SphinxException as sphinxException:
                subpage.delete()
                return render_to_response('subpage_add.html', { 'fid' : fid,
                                                                'form' : form, 
                                                                'page_info' : page_info,
                                                                'sphinxException' : sphinxException })
            except e:
                subpage.delete()
                raise e
            return HttpResponseRedirect(reverse('subpage',args=[subpage.id]))
    else:
        #TODO(kalq): Create a hash instead of full pathname
        fid = tempfile.mkdtemp()
        form = GlobalSubpageEditForm(initial={ 'fid' : fid })
    return render_to_response('subpage_add.html', { 'fid' : fid,
                                                    'form' : form,
                                                    'page_info' : page_info })

@general_view
def edit(request, page_info, id):
    subpage = Subpage.filter(SubpageStruct(id=int(id)))[0]
    if request.method=="POST":
        if 'delete' in request.POST.keys():
            subpage.delete()
            return HttpResponseRedirect(reverse('news'))
        form = GlobalSubpageEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            fid = data['fid']
            for rfile in request.POST:
                if rfile.startswith('rfile'):
                    subpage.content_files_delete(request.POST[rfile])
            for ufile in glob.glob(os.path.join(fid, '*')):
                subpage.content_files_set_blob_path(os.path.basename(ufile), ufile)
            try:
                subpage.modify(SubpageStruct(name=data['name'],
                                             content=data['content'],
                                             is_public=data['is_public']))
            except SphinxException as sphinxException:
                attachments = valid_attachments(subpage.content_files_get_list())
                return render_to_response('subpage_edit.html', { 'attachments' : attachments,
                                                                 'fid' : fid,
                                                                 'form' : form,
                                                                 'page_info' : page_info,
                                                                 'sphinxException' : sphinxException,
                                                                 'subpage' : subpage })
            return HttpResponseRedirect(reverse('subpage',args=[subpage.id]))
    else:
        fid = tempfile.mkdtemp()
        form = GlobalSubpageEditForm(initial={ 'name' : subpage.name,
                                               'content' : subpage.content,
                                               'fid' : fid,
                                               'is_public' : subpage.is_public })
    attachments = valid_attachments(subpage.content_files_get_list())
    return render_to_response('subpage_edit.html', { 'attachments' : attachments, 
                                                     'fid' : fid,
                                                     'form' : form,
                                                     'page_info' : page_info,
                                                     'subpage' : subpage })
