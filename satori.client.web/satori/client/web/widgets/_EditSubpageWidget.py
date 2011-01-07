from copy import deepcopy
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

class EditSubpageWidget(Widget):
    pathName = 'editsubpage'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/editsubpage.html'
        self.contest = ActiveContest(params)
        self.canglobal = Allowed('global','ADMIN')
        d = follow(params,path)
        if 'edit' in d.keys():
            self.editing = Subpage.filter({'id' : int(d['edit'][0])})[0]
        self.back_to = ToString(params);
        