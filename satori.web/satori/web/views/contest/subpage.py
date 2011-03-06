# vim:ts=4:sts=4:sw=4:expandtab
import glob
import os
import tempfile
from satori.client.common import want_import
want_import(globals(), '*')
from satori.web.utils.decorators import contest_view
from satori.web.utils.shortcuts import fill_image_links
from satori.web.utils.shortcuts import render_to_json, text2html
from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

class ContestSubpageEditForm(forms.Form):
    name = forms.CharField(label="Subpage name")
    content = forms.CharField(required=False,widget=forms.Textarea, label="Content")
    is_public = forms.BooleanField(label="Show to all visitors", required=False)

@contest_view
def view(request, page_info,id):
    sinfo = Web.get_subpage_info(Subpage(int(id)))
    content = fill_image_links(sinfo.html, 'Subpage', id, 'content_files')
    can_edit = sinfo.subpage.contest and sinfo.is_admin
    return render_to_response('subpage.html',{'page_info' : page_info, 'subpage' : sinfo.subpage, 'content' : content, 'can_edit' : can_edit})
    subpage = Subpage.filter(SubpageStruct(id=int(id)))[0]

@contest_view
def create(request, page_info):
    if request.method=="POST":
        form = ContestSubpageEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            fid = request.POST["fid"]
            subpage = Subpage.create_for_contest(SubpageStruct(is_announcement=False,contest=page_info.contest,name=data["name"],content=''))
            for ufile in glob.glob(os.path.join(fid, '*')):
                subpage.content_files_set_blob_path(os.path.basename(ufile), ufile)
            subpage.content = data["content"]
            return HttpResponseRedirect(reverse('contest_subpage',args=[page_info.contest.id, subpage.id]))
    else:
        form = ContestSubpageEditForm()
        temp_directory = tempfile.mkdtemp()
        fid = temp_directory #TODO(kalq): Create a hash instead of full pathname
    return render_to_response('subpage_create.html',{'page_info' : page_info, 'form' : form, 'fid' : fid})

@contest_view
def edit(request, page_info,id):
    subpage = Subpage.filter(SubpageStruct(id=int(id)))[0]
    if request.method=="POST":
        form = ContestSubpageEditForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            fid = request.POST["fid"]
            for rfile in request.POST:
                if rfile.startswith('rfile'):
                    subpage.content_files_delete(request.POST[rfile])
            for ufile in glob.glob(os.path.join(fid, '*')):
                subpage.content_files_set_blob_path(os.path.basename(ufile), ufile)
            subpage.modify(SubpageStruct(name=data["name"],content=data["content"],is_public=data["is_public"]))
            return HttpResponseRedirect(reverse('contest_subpage',args=[page_info.contest.id, subpage.id]))
    else:
        form = ContestSubpageEditForm(initial={'name' : subpage.name, 'content' : subpage.content, 'is_public' : subpage.is_public})
        dfiles = []
        for dfile in subpage.content_files_get_list():
            if not (dfile.name == '_html' or dfile.name == '_pdf' or dfile.name.startswith('_img_')):
                dfiles.append(dfile.name)
#            f.name, f.is_blob, equals('_html'), equals('_pdf'), startswith('_img_')
        temp_directory = tempfile.mkdtemp()
        fid = temp_directory #TODO(kalq): Create a hash instead of full pathname
    return render_to_response('subpage_edit.html',{'page_info' : page_info, 'form' : form, 'subpage' : subpage, 'attachments' : dfiles, 'fid' : fid})

@contest_view
def delete(request, page_info,id):
    subpage = Subpage.filter(SubpageStruct(id=int(id)))[0]
    name = subpage.name
    content = subpage.content
    return render_to_response('subpage.html',{'page_info' : page_info, 'name' : name, 'content' : content})

@contest_view
def fileupload(request, page_info):
    if request.method=="POST":
        ufile = request.FILES['file']
        f = open(os.path.join(request.POST['fid'], ufile.name), 'w')
        f.write(ufile.read())
        f.close()
        return render_to_json('json/contest_fileupload.json', {'page_info' : page_info, 'name' : ufile.name})
    # TODO(kalq) return 404

# This function is used only to delete temporary files - (those that aren't
# inside core yet).
@contest_view
def fileremove(request, page_info):
    print request
    if request.method=="POST":
        rfile = request.POST['filename']
        # TODO(kalq): Add some exception handling here.
        os.remove(os.path.join(request.POST['fid'], rfile))
        return render_to_json('json/contest_fileremove.json', {'page_info' : page_info, 'name' : rfile})
    # TODO(kalq): return 404

