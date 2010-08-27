from copy import deepcopy
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from satori.client.web.postmarkup import render_bbcode
from _Widget import Widget

class ManageNewsWidget(Widget):
    pathName = 'mannews'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/mannews.html'
        self.contest = ActiveContest(params)
        self.canglobal = Allowed(True,'managenews')
        self.messages = []
        d = follow(params,path)
        _params = deepcopy(params)
        _d = follow(_params,path)
        if 'edit' in d.keys():
            self.editing = True
            try:
                msg = MessageGlobal(d['edit'][0])
            except MessageGlobal.DoesNotExist:
                msg = MessageContest(d['edit'][0])
            self.msgtopic = msg.topic
            self.msgcontent = msg.content
            self.msgid = msg.id
            del _d['edit'];
        self.back_to = ToString(_params);
        for m in MessageGlobal.filter():
            if not ActiveContest(params) or not m.mainscreenonly:
                self.messages.append({'id' : m.id, 'type' : 'global', 'topic' : m.topic, 'content' : render_bbcode(m.content), 'time' : m.time, 'canedit' : Allowed(m,'edit')})
        for m in MessageContest.filter({'contest':ActiveContest(params)}):
                self.messages.append({'id' : m.id, 'type' : 'contest', 'topic' : m.topic, 'content' : render_bbcode(m.content), 'time' : m.time, 'canedit' : Allowed(m,'edit')})
        for md in self.messages:
            if md['canedit']:
                _d['edit'] = [str(md['id'])]
                md['editlink'] = GetLink(_params,'')
