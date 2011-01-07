from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

from docutils.core import publish_parts

# ranking (a possible main content)
class RankingWidget(Widget):
    pathName = 'ranking'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/ranking.html'
        d = follow(params,path)
        r = Ranking.filter({'id' : int(d['subid'][0])})[0]
        self.name = r.name
        self.content = text2html(r.full_ranking())
