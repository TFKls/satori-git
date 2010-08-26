from satori.client.web.widgets import Widget

# about table (to test ajah)
class AboutWidget(Widget):
    pathName = 'about'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/about.html'

