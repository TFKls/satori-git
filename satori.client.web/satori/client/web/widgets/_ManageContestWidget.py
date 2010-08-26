from satori.client.web.widgets import Widget

class ManageContestWidget(Widget):
    pathName = 'mancontest'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/mancontest.html'
