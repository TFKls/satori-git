import os
from satori.web.sphinx.translator import rendertask
from satori.web.urls import PROJECT_PATH
from django.core.urlresolvers import reverse
import re

def text2html(text):
    return rendertask(unicode(text), os.path.join(PROJECT_PATH, 'files/tmp'), 'files/tmp')
    
def fill_image_links(content, model, id, group):
    def imagerepl(matchobj):
        return '"' + reverse('download_group', args=['view', model, id, group, matchobj.group(1), matchobj.group(1)]) + '"'
    return re.sub(r'"_images/([^"]+)"', imagerepl, content)

