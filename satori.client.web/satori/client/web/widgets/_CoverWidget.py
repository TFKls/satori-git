from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from _Widget import Widget

# cover widget
class CoverWidget(Widget):
    pathName = 'cover'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/cover.html'
        d = DefaultLayout(params)
        self.cover = Widget.FromDictionary(params,'cover(0)');
