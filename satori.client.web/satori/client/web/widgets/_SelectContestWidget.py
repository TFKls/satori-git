from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

# contest selection screen (a possible main content)
class SelectContestWidget(Widget):
    pathName = 'selectcontest'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/selectcontest.html'
        self.contests = []
        self.user = CurrentUser()
        self.back_to = ToString(params)
        self.path = path
        self.cancreate = Allowed('global','ADMIN')
        for c in Contest.filter():
            cu = MyContestant(c)
            d = DefaultLayout()
            d['contestid'] = [str(c.id)]
            con = { 'obj' : c,
                    'status' : 0,
                    'link' : GetLink(d,'')}

            if not cu:
                if Allowed(c,"APPLY"):
                    con['status'] = 2
                else:
                    con['status'] = 3
            else:
                if not cu.accepted:
                    con['status'] = 1
            self.contests.append(con)
