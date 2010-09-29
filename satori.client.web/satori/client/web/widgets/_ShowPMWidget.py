from satori.client.web.queries import *
from satori.client.web.URLDictionary import *
from _Widget import Widget

class ShowPMWidget(Widget):
    pathName = 'showpm'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/showpm.html'
        d = follow(params,path)
        pm = ProblemMapping.filter({'id' : int(d['problemid'][0])})[0]
        self.pm = pm
        self.back_to = ToString(params)
        self.statement = text2html(pm.statement_get_str('text'))
