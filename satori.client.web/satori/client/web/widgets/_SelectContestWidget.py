from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

# contest selection screen (a possible main content)
class SelectContestWidget(Widget):
    pathName = 'selectcontest'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/selectcontest.html'
        self.participating = []
        self.mayjoin = []
        self.other = []
        self.user = CurrentUser()
        self.back_to = ToString(params)
        self.path = path
        self.cancreate = Allowed('global','ADMIN')
        for c in Contest.filter():
            cu = MyContestant(c)
            d = DefaultLayout()
            d['contestid'] = [str(c.id)]
            if cu:
                self.participating.append([c,cu,GetLink(d,'')])
            else:
                mayjoin = Allowed(c,"APPLY")
                self.other.append([c,mayjoin,GetLink(d,'')])
