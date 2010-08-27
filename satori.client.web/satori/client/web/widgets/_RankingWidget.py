from _Widget import Widget

# ranking (a possible main content)
class RankingWidget(Widget):
    pathName = 'ranking'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/ranking.html'
