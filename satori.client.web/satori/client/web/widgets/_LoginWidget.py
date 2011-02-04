from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common import want_import
want_import(globals(), '*')
from _Widget import Widget

# login box
class LoginWidget(Widget):
    pathName = 'loginform'
    def __init__(self, params, path):
        el = CurrentUser()
        if el:
            self.htmlFile = 'htmls/logged.html'
            self.status = follow(params, path).get('status')
            if self.status:
                self.status = self.status[0]
            self.name = el.name
        else:
            self.htmlFile = 'htmls/loginform.html'
            self.back_to = ToString(params)
            self.lw_path = path
            self.status = follow(params, path).get('status')
            if self.status:
                self.status = self.status[0]
