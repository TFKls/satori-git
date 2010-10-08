from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

from docutils.core import publish_parts

# news table (a possible main content)
class NewsWidget(Widget):
    pathName = 'news'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/news.html'
        self.messages = []
        for m in MessageGlobal.filter():
            if not ActiveContest(params) or not m.mainscreenonly:
                self.messages.append({'time' : m.time, 'type' : 'global', 'topic' : m.topic, 'content' : publish_parts(m.content, writer_name='html')['fragment']})
        if (ActiveContest(params)):
            for m in MessageContest.filter({'contest':ActiveContest(params)}):
                self.messages.append({'time' : m.time, 'type' : 'contest', 'topic' : m.topic, 'content' : publish_parts(m.content, writer_name='html')['fragment']})
        self.messages.sort(key=lambda msg: msg['time'], reverse=True)

