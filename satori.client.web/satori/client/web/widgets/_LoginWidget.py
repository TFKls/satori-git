from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common import *
from satori.client.web.widgets import Widget

# login box
class LoginWidget(Widget):
    pathName = 'loginform'
    def __init__(self, params, path):
        el = CurrentUser()
        if el:
            self.htmlFile = 'htmls/logged.html'
            self.name = el.fullname
        else:
            self.htmlFile = 'htmls/loginform.html'
            self.back_to = ToString(params)
            self.lw_path = path
