# vim:ts=4:sts=4:sw=4:expandtab
import glob
import os
import tempfile
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.files import mkdtemp, valid_attachments
from satori.web.utils.forms import SatoriSignedField
from satori.web.utils.shortcuts import fill_image_links
from satori.web.utils.shortcuts import render_to_json, text2html
from satori.web.utils.rights import RightsTower
from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response


rights = RightsTower(label='Visible for')
rights.choices = ['Everyone','Contestants','Admins only']
rights.rights = ['VIEW','VIEW','']

class ContestSubpageEditForm(forms.Form):
    name = forms.CharField(label="Subpage name")
    visibility = rights.field()
    fid = SatoriSignedField(required=True) # (temporary) folder id
    content = forms.CharField(required=False, widget=forms.Textarea, label="Content")

@contest_view
def view(request, page_info,id):
    sinfo = Web.get_subpage_info(Subpage(int(id)))
    attachments = valid_attachments(sinfo.subpage.content_files_get_list())
    content = fill_image_links(unicode(sinfo.html), 'Subpage', id, 'content_files')
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
            rights.roles = [Security.anonymous(),contest.contestant_role,None]
            rights.objects = [subpage,subpage,None]
            rights.set(int(data['visibility']))                                                               
            for ufile in glob.glob(os.path.join(fid, '*')):
                subpage.content_files_set_blob_path(os.path.basename(ufile), ufile)
            try:
                subpage.content = data["content"]
            except SphinxException as sphinxException:
                subpage.delete()
                form._errors['content'] = form.error_class([sphinxException])
                return render_to_response('subpage_add.html', { 'fid' : fid,
                                                                'form' : form, 
                                                                'page_info' : page_info })
            except e:
                subpage.delete()
                raise e
            return HttpResponseRedirect(reverse('contest_subpage', args=[page_info.contest.id, subpage.id]))
    else:
        #TODO(kalq): Create a hash instead of full pathname
        fid = mkdtemp()
        form = ContestSubpageEditForm(initial={ 'fid' : fid })
    return render_to_response('subpage_add.html', { 'fid' : fid,
                                                    'form' : form,
                                                    'page_info' : page_info })

@contest_view
def edit(request, page_info,id):

    contest = page_info.contest
    subpage = Subpage.filter(SubpageStruct(id=int(id)))[0]
    rights.roles = [Security.anonymous(),contest.contestant_role,None]
    rights.objects = [subpage,subpage,None]
    rights.check()
    
    class ContestSubpageEditForm(forms.Form):
        name = forms.CharField(label="Subpage name")
        visibility = rights.field()
        fid = SatoriSignedField(required=True) # (temporary) folder id
        content = forms.CharField(required=False, widget=forms.Textarea, label="Content")
    
    if request.method=="POST":
        form = ContestSubpageEditForm(request.POST)
        if form.is_valid():
            if 'delete' in request.POST.keys():
                subpage.delete()
                return HttpResponseRedirect(reverse('contest_manage',args=[contest.id]))
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
                vis = data['visibility']
                rights.set(vis)


            except SphinxException as sphinxException:
                attachments = valid_attachments(subpage.content_files_get_list())
                form._errors['content'] = form.error_class([sphinxException])
                return render_to_response('subpage_edit.html', { 'attachments' : attachments,
                                                                 'fid' : fid,
                                                                 'form' : form,
                                                                 'page_info' : page_info,
                                                                 'subpage' : subpage })
            return HttpResponseRedirect(reverse('contest_subpage', args=[page_info.contest.id, subpage.id]))
    else:
        vis = unicode(rights.current)
        fid = mkdtemp()
        form = ContestSubpageEditForm(initial={ 'name' : subpage.name,
                                                'content' : subpage.content,
                                                'fid' : fid,
                                                'visibility' : vis
                                                })
    attachments = valid_attachments(subpage.content_files_get_list())
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
