from _Widget import Widget
from satori.client.web.queries import *

class ManageContestWidget(Widget):
    pathName = 'mancontest'
    def __init__(self, params, path):
        c = ActiveContest(params)
        self.subpages = []
        for s in Subpage.filter({'contest':c}):
            editlink = ToString(DefaultLayout(dict=params,maincontent='editsubpage',subid=[str(s.id)]))
            self.subpages.append([s,editlink])
        self.htmlFile = 'htmls/mancontest.html'
