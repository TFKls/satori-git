from copy import deepcopy
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common import want_import
want_import(globals(), '*')
from _Widget import Widget

class ManageNewsWidget(Widget):
    pathName = 'mannews'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/mannews.html'
        self.contest = ActiveContest(params)
        self.canglobal = Allowed('global','ADMIN')
        d = follow(params,path)
        _params = deepcopy(params)
        _d = follow(_params,path)
        if 'edit' in d.keys():
            self.editing = Subpage.filter({'id' : int(d['edit'][0])})[0]
            if not self.editing.is_announcement:
                raise ''
            del _d['edit']
        self.back_to = ToString(_params);
        c = ActiveContest(params)
        if c:
            allmsg = Subpage.get_for_contest(c,True)
        else:
            allmsg = Subpage.get_global(True)
        allmsg.sort(key=lambda msg : msg.date_created, reverse=True)
        self.messages = []
        for m in allmsg:
            self.messages.append({'m' : m, 'canedit' : Allowed(m,'MANAGE'), 'content' : text2html(m.content)})
        for md in self.messages:
            if md['canedit']:
                _d['edit'] = [str(md['m'].id)]
                md['editlink'] = GetLink(_params,'')
#        for m in MessageGlobal.filter():
#            if not ActiveContest(params) or not m.mainscreenonly:
#                self.messages.append({'id' : m.id, 'type' : 'global', 'topic' : m.topic, 'content' : m.content, 'time' : m.time, 'canedit' : Allowed(m,'edit')})
#        if ActiveContest(params):
#            for m in MessageContest.filter({'contest':ActiveContest(params)}):
#                    self.messages.append({'id' : m.id, 'type' : 'contest', 'topic' : m.topic, 'content' : m.content, 'time' : m.time, 'canedit' : Allowed(m,'edit')})
        