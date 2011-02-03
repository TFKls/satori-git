from satori.client.web.queries import *
from satori.client.common import want_import
want_import(globals(), '*')
from _Widget import Widget

from docutils.core import publish_parts

# news table (a possible main content)
class NewsWidget(Widget):
    pathName = 'news'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/news.html'
        c = ActiveContest(params)
        if c:
            messages = Subpage.get_for_contest(c, True)
        else:
            messages = Subpage.get_global(True)
        self.allmsg = []
        for m in messages:
            self.allmsg.append({'m' : m, 'content' : text2html(m.content)})
#        for m in MessageGlobal.filter():
#            if not ActiveContest(params) or not m.mainscreenonly:
#                
#        if (ActiveContest(params)):
#            for m in MessageContest.filter({'contest':ActiveContest(params)}):
#                self.messages.append({'time' : m.time, 'type' : 'contest', 'topic' : m.topic, 'content' : publish_parts(m.content, writer_name='html')['fragment']})
        self.allmsg.sort(key=lambda msg: msg['m'].date_created, reverse=True)

