from _Widget import Widget
from satori.client.web.queries import *

class ManageContestWidget(Widget):
    pathName = 'mancontest'
    def __init__(self, params, path):
        c = ActiveContest(params)
        self.subpages = []
        for s in Subpage.get_for_contest(c,False):
            editlink = ToString(DefaultLayout(dict=params,maincontent='editsubpage',edit=[str(s.id)]))
            self.subpages.append([s,editlink])
        self.subpages.sort(key=lambda s : s[0].order)
        self.addlink = ToString(DefaultLayout(dict=params,maincontent='editsubpage'))
        self.htmlFile = 'htmls/mancontest.html'
