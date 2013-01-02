# vim:ts=4:sts=4:sw=4:expandtab
import glob
import os
import tempfile
from satori.web.utils.forms import SatoriSignedField
from satori.web.utils.decorators import general_view
from satori.web.utils.shortcuts import render_to_json, text2html
from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

class FileUploadForm(forms.Form):
    fid = SatoriSignedField(required=True) # (temporary) folder id
    file = forms.FileField(required=True)

@general_view
def fileupload(request, page_info):
    if request.method=="POST":
        form = FileUploadForm(request.POST, request.FILES)
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

class FileRemoveForm(forms.Form):
    fid = SatoriSignedField(required=True) # (temporary) folder id
    filename = forms.CharField(required=True)

# This function is used only to delete temporary files - (those that aren't inside core yet).
@general_view
def fileremove(request, page_info):
    if request.method=="POST":
        form = FileRemoveForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            fid, rfile = data['fid'], data['filename']
            # TODO(kalq): Add some exception handling here.
            os.remove(os.path.join(fid, rfile))
            return render_to_json('json/global_fileremove.json', {'page_info' : page_info, 'name' : rfile})
        #TODO(kalq): return error code
    # TODO(kalq): return 404

def valid_attachments(attachments):
    dfiles = []
    for dfile in attachments:
        if not (dfile.name == '_html' or dfile.name == '_pdf' or dfile.name.startswith('_img_')) and dfile.is_blob:
            dfiles.append(dfile.name)
    return dfiles
