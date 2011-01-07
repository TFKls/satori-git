from satori.client.web.queries import *
from satori.client.web.URLDictionary import *
from _Widget import Widget

class SubpageWidget(Widget):
    pathName = 'subpage'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/subpage.html'
        d = follow(params,path)
        s = Subpage.filter({'id' : int(d['subid'][0])})[0]
        self.name = s.name
        self.content = text2html(s.content)
