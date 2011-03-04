import os
from satori.web.sphinx.translator import rendertask
from satori.web.urls import PROJECT_PATH

def text2html(text):
    return rendertask(unicode(text), os.path.join(PROJECT_PATH, 'files/tmp'), 'files/tmp')
    

