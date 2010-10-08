from copy import deepcopy
from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

class ManageNewsWidget(Widget):
    pathName = 'mannews'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/mannews.html'
        self.contest = ActiveContest(params)
        self.canglobal = Allowed('global','ADMIN')
        self.messages = []
        d = follow(params,path)
        _params = deepcopy(params)
        _d = follow(_params,path)
        if 'edit' in d.keys():
            self.editing = True
            try:
                msg = MessageGlobal.filter({'id' : int(d['edit'][0])})[0]
            except:
                msg = MessageContest.filter({'id' : int(d['edit'][0])})[0]
            self.msgtopic = msg.topic
            self.msgcontent = msg.content
            self.msgid = msg.id
            del _d['edit'];
        self.back_to = ToString(_params);
        for m in MessageGlobal.filter():
            if not ActiveContest(params) or not m.mainscreenonly:
                self.messages.append({'id' : m.id, 'type' : 'global', 'topic' : m.topic, 'content' : text2html(m.content), 'time' : m.time, 'canedit' : Allowed(m,'edit')})
        if ActiveContest(params):
            for m in MessageContest.filter({'contest':ActiveContest(params)}):
                    self.messages.append({'id' : m.id, 'type' : 'contest', 'topic' : m.topic, 'content' : text2html(m.content), 'time' : m.time, 'canedit' : Allowed(m,'edit')})
        for md in self.messages:
            if md['canedit']:
                _d['edit'] = [str(md['id'])]
                md['editlink'] = GetLink(_params,'')
        self.messages.sort(key=lambda msg : msg['time'], reverse=True)
