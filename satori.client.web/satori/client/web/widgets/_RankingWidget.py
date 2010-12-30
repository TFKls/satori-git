from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

from docutils.core import publish_parts

# ranking (a possible main content)
class RankingWidget(Widget):
    pathName = 'ranking'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/ranking.html'
        self.rankings = []
        if (ActiveContest(params)):
            for r in Ranking.filter({'contest':ActiveContest(params)}):
                self.rankings.append({'content' : publish_parts(r.full_ranking(), writer_name='html')['fragment']})
