# vim:ts=4:sts=4:sw=4:expandtab
import glob
import os
import tempfile
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import general_view
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

def valid_attachments(subpage):
    dfiles = []
    for dfile in subpage.content_files_get_list():
        if not (dfile.name == '_html' or dfile.name == '_pdf' or dfile.name.startswith('_img_')) and dfile.is_blob:
            dfiles.append(dfile.name)
    return dfiles

@general_view
def view(request, page_info,id):
    sinfo = Web.get_subpage_info(Subpage(int(id)))
    attachments = valid_attachments(sinfo.subpage)
    content = fill_image_links(sinfo.html, 'Subpage', id, 'content_files')
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
                                                               name=data['name']))
            for ufile in glob.glob(os.path.join(fid, '*')):
                subpage.content_files_set_blob_path(os.path.basename(ufile), ufile)
            try:
                subpage.content = data["content"]
            except SphinxException as sphinxException:
                return render_to_response('subpage_add.html', { 'form' : form, 
                                                                   'page_info' : page_info,
                                                                   'sphinxException' : sphinxException })
            return HttpResponseRedirect(reverse('subpage',args=[subpage.id]))
    else:
        #TODO(kalq): Create a hash instead of full pathname
        form = GlobalSubpageEditForm(initial={ 'fid' : tempfile.mkdtemp() })
    return render_to_response('subpage_add.html', { 'form' : form,
                                                       'page_info' : page_info })

@general_view
def edit(request, page_info,id):
    subpage = Subpage.filter(SubpageStruct(id=int(id)))[0]
    if request.method=="POST":
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
                attachments = valid_attachments(subpage)
                return render_to_response('subpage_edit.html', { 'attachments' : attachments,
                                                                 'form' : form,
                                                                 'page_info' : page_info,
                                                                 'sphinxException' : sphinxException,
                                                                 'subpage' : subpage })
            return HttpResponseRedirect(reverse('subpage',args=[subpage.id]))
    else:
        form = GlobalSubpageEditForm(initial={ 'name' : subpage.name,
                                               'content' : subpage.content,
                                               'fid' : tempfile.mkdtemp(),
                                               'is_public' : subpage.is_public })
    attachments = valid_attachments(subpage)
    return render_to_response('subpage_edit.html', { 'attachments' : attachments, 
                                                     'form' : form,
                                                     'page_info' : page_info,
                                                     'subpage' : subpage })

class GlobalSubpageUploadForm(forms.Form):
    fid = forms.CharField(required=True, widget=forms.HiddenInput) # (temporary) folder id
    file = forms.FileField(required=True)

@general_view
def fileupload(request, page_info):
    if request.method=="POST":
        form = GlobalSubpageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            fid, ufile = data['fid'], data['file']
            #TODO(kalq): add some error handling if directory doesn't exist
            f = open(os.path.join(fid, ufile.name), 'w')
            f.write(ufile.read())
            f.close()
            return render_to_json('json/global_fileupload.json', {'page_info' : page_info, 'name' : ufile.name})
        #TODO(kalq): return error code
    # TODO(kalq): return 404

class GlobalSubpageRemoveForm(forms.Form):
    fid = forms.CharField(required=True, widget=forms.HiddenInput) # (temporary) folder id
    filename = forms.CharField(required=True)

# This function is used only to delete temporary files - (those that aren't inside core yet).
@general_view
def fileremove(request, page_info):
    if request.method=="POST":
        form = GlobalSubpageRemoveForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            fid, rfile = data['fid'], data['filename']
            # TODO(kalq): Add some exception handling here.
            os.remove(os.path.join(fid, rfile))
            return render_to_json('json/global_fileremove.json', {'page_info' : page_info, 'name' : rfile})
        #TODO(kalq): return error code
    # TODO(kalq): return 404
