# vim:ts=4:sts=4:sw=4:expandtab
import glob
import os
import tempfile
from satori.web.utils.forms import SatoriSignedField
from satori.web.utils.decorators import general_view
from satori.web.utils.shortcuts import render_to_json, text2html
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response

tempdir = settings.FILE_UPLOAD_TEMP_DIR
prefix = 'satori-temp-upload'

def mkdtemp():
    return os.path.realpath(os.path.abspath(tempfile.mkdtemp(prefix=prefix, dir=tempdir)))

def validate_filename(value):
    try:
        login.decode('ascii')
    except:
        raise ValidationError(u'filename \'%s\' contains invalid characters' % value)
    for l in login:
        if not (l.isalpha() or l.isdigit() or l == '_' or l == "."):
            raise ValidationError(u'filename \'%s\' contains invalid characters' % value)

def validate_file(value):
    validate_filename(value.name)

def validate_path(value):
    if not os.path.isabs(value):
        raise ValidationError(u'path \'%s\' is not absolute' % value)
    value = os.path.realpath(value)
    if tempdir is not None:
        if not value[0:len(tempdir)] != tempdir:
            raise ValidationError(u'path \'%s\' was malformed' % value)
    if os.path.basename(value)[0:len(prefix)] != prefix:
        raise ValidationError(u'path \'%s\' was malformed' % value)
    if not os.path.exists(value) or os.path.islink(value) or not os.path.isdir(value):
        raise ValidationError(u'path \'%s\' does not exist' % value)

class FileUploadForm(forms.Form):
    fid = SatoriSignedField(required=True, validators=[validate_path]) # (temporary) folder id
    file = forms.FileField(required=True, validators=[validate_file])

@general_view
def fileupload(request, page_info):
    if request.method=="POST":
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            fid, ufile = data['fid'], data['file']
            f = open(os.path.join(fid, ufile.name), 'w')
            f.write(ufile.read())
            f.close()
            return render_to_json('json/global_fileupload.json', {'page_info' : page_info, 'name' : ufile.name})
    return HttpResponseNotFound('')

class FileRemoveForm(forms.Form):
    fid = SatoriSignedField(required=True, validators=[validate_path]) # (temporary) folder id
    filename = forms.CharField(required=True, validators=[validate_filename])

# This function is used only to delete temporary files - (those that aren't inside core yet).
@general_view
def fileremove(request, page_info):
    if request.method=="POST":
        form = FileRemoveForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            fid, rfile = data['fid'], data['filename']
            rf = os.path.join(fid, rfile)
            if os.path.exists(rf):
                os.remove(rf)
            return render_to_json('json/global_fileremove.json', {'page_info' : page_info, 'name' : rfile})
    return HttpResponseNotFound('')

def valid_attachments(attachments):
    dfiles = []
    for dfile in attachments:
        if not (dfile.name == '_html' or dfile.name == '_pdf' or dfile.name.startswith('_img_')) and dfile.is_blob:
            dfiles.append(dfile.name)
    return dfiles
