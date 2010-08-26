from satori.client.web.queries import *
from satori.client.common import *
from satori.client.web.widgets import Widget

# news table (a possible main content)
class NewsWidget(Widget):
    pathName = 'news'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/news.html'
        self.messages = []
        for m in MessageGlobal.filter():
            if not ActiveContest(params) or not m.mainscreenonly:
                self.messages.append({'type' : 'global', 'topic' : m.topic, 'content' : render_bbcode(m.content)})
        if (ActiveContest(params)):
            for m in MessageContest.filter(contest = ActiveContest(params)):
                self.messages.append({'type' : 'contest', 'topic' : m.topic, 'content' : render_bbcode(m.content)})
