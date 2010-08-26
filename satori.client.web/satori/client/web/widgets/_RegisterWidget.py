from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common import *
from satori.client.web.widgets import Widget

# register box
class RegisterWidget(Widget):
    pathName = 'registerform'
    def __init__(self, params, path):
        el = CurrentUser()
        if el:
            self.htmlFile = 'htmls/logged.html'
            self.name = el.fullname
        else:
            self.htmlFile = 'htmls/registerform.html'
            self.back_to = ToString(params)
            self.lw_path = path
