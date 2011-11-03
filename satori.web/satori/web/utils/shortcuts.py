import re
import os
from docutils.core import publish_parts
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from satori.web.urls import PROJECT_PATH

def fill_image_links(content, model, id, group):
    def imagerepl(matchobj):
        return '"' + reverse('download_group', args=['view', model, id, group, matchobj.group(1), matchobj.group(1)]) + '"'
    return re.sub(r'"_images/([^"]+)"', imagerepl, content)

def render_to_json(*args, **kwargs):
    response = render_to_response(*args, **kwargs)
    response['mimetype'] = "text/javascript"
    response['Pragma'] = "no cache"
    response['Cache-Control'] = "no-cache, must-revalidate"

    return response

def text2html(text):
    return '<div class="mainsphinx">'+publish_parts(text,writer_name='html')['fragment']+'</div>'

