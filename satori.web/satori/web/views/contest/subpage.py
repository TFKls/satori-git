# vim:ts=4:sts=4:sw=4:expandtab
import glob
import os
import tempfile
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.files import valid_attachments
from satori.web.utils.shortcuts import fill_image_links
from satori.web.utils.shortcuts import render_to_json, text2html
from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

class ContestSubpageEditForm(forms.Form):
    name = forms.CharField(label="Subpage name")
    visibility = forms.ChoiceField(label="Visible for", required=True, choices=[['admin','Admins only'],['contestant','Contestants'],['public', 'Everyone']]) 
    fid = forms.CharField(required=True, widget=forms.HiddenInput) # (temporary) folder id
    content = forms.CharField(required=False, widget=forms.Textarea, label="Content")

@contest_view
def view(request, page_info,id):
    sinfo = Web.get_subpage_info(Subpage(int(id)))
    attachments = valid_attachments(sinfo.subpage)
    content = fill_image_links(sinfo.html, 'Subpage', id, 'content_files')
    can_edit = sinfo.subpage.contest and sinfo.is_admin

    return render_to_response('subpage.html', { 'attachments' : attachments,
                                                'can_edit' : can_edit,
                                                'content' : content,
                                                'page_info' : page_info, 
                                                'subpage' : sinfo.subpage })

@contest_view
def add(request, page_info):
    contest = page_info.contest
    if request.method=="POST":
        form = ContestSubpageEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            fid = data['fid']
            subpage = Subpage.create_for_contest(SubpageStruct(is_announcement=False,
                                                               content='',
                                                               contest=page_info.contest,
                                                               name=data['name']))
                                                               
            vis = data["visibility"]
            if vis=='public':
                Privilege.grant(contest.contestant_role,subpage,'VIEW')
                subpage.is_public = True
            elif vis=='contestant':
                Privilege.grant(contest.contestant_role,subpage,'VIEW')
                subpage.is_public = False
            else:
                Privilege.revoke(contest.contestant_role,subpage,'VIEW')
                subpage.is_public = False                                                               
            
            for ufile in glob.glob(os.path.join(fid, '*')):
                subpage.content_files_set_blob_path(os.path.basename(ufile), ufile)
            try:
                subpage.content = data["content"]
            except SphinxException as sphinxException:
                return render_to_response('subpage_add.html', { 'fid' : fid,
                                                                'form' : form, 
                                                                'page_info' : page_info,
                                                                'sphinxException' : sphinxException })
            return HttpResponseRedirect(reverse('contest_subpage', args=[page_info.contest.id, subpage.id]))
    else:
        #TODO(kalq): Create a hash instead of full pathname
        fid = tempfile.mkdtemp()
        form = ContestSubpageEditForm(initial={ 'fid' : fid })
    return render_to_response('subpage_add.html', { 'fid' : fid,
                                                    'form' : form,
                                                    'page_info' : page_info })

@contest_view
def edit(request, page_info,id):
    contest = page_info.contest
    subpage = Subpage.filter(SubpageStruct(id=int(id)))[0]
    if request.method=="POST":
        form = ContestSubpageEditForm(request.POST)
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
                                             content=data['content']))

                vis = data["visibility"]
                if vis=='public':
                    Privilege.grant(contest.contestant_role,subpage,'VIEW')
                    subpage.is_public = True
                elif vis=='contestant':
                    Privilege.grant(contest.contestant_role,subpage,'VIEW')
                    subpage.is_public = False
                else:
                    Privilege.revoke(contest.contestant_role,subpage,'VIEW')
                    subpage.is_public = False                                                               


            except SphinxException as sphinxException:
                attachments = valid_attachments(subpage)
                return render_to_response('subpage_edit.html', { 'attachments' : attachments,
                                                                 'fid' : fid,
                                                                 'form' : form,
                                                                 'page_info' : page_info,
                                                                 'sphinxException' : sphinxException,
                                                                 'subpage' : subpage })
            return HttpResponseRedirect(reverse('contest_subpage', args=[page_info.contest.id, subpage.id]))
    else:
        if subpage.is_public:
            vis = 'public'
        elif Privilege.get(contest.contestant_role,subpage,'VIEW'):
            vis = 'contestant'
        else:
            vis = 'admin'
        fid = tempfile.mkdtemp()
        form = ContestSubpageEditForm(initial={ 'name' : subpage.name,
                                                'content' : subpage.content,
                                                'fid' : fid,
                                                'visibility' : vis
                                                })
    attachments = valid_attachments(subpage)
    return render_to_response('subpage_edit.html', { 'attachments' : attachments, 
                                                     'fid' : fid,
                                                     'form' : form,
                                                     'page_info' : page_info,
                                                     'subpage' : subpage })

#TODO(kalq): Do something with this function.
#@contest_view
#def delete(request, page_info,id):
#    subpage = Subpage.filter(SubpageStruct(id=int(id)))[0]
#    name = subpage.name
#    content = subpage.content
#    return render_to_response('subpage.html',{'page_info' : page_info, 'name' : name, 'content' : content})
