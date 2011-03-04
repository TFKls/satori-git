import os
from django.shortcuts import render_to_response
from satori.web.sphinx.translator import rendertask
from satori.web.urls import PROJECT_PATH

def render_to_json(*args, **kwargs):
    response = render_to_response(*args, **kwargs)
    response['mimetype'] = "text/javascript"
    response['Pragma'] = "no cache"
    response['Cache-Control'] = "no-cache, must-revalidate"

    return response

def text2html(text):
    return rendertask(unicode(text), os.path.join(PROJECT_PATH, 'files/tmp'), 'files/tmp')

