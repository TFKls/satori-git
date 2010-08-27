from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget
from _LoginWidget import LoginWidget
from _HeaderWidget import HeaderWidget
from _MenuWidget import MenuWidget

# base widget
class MainWidget(Widget):
    pathName = 'main'
    def __init__(self, params, path):
        _params = follow(params,path)
        self.htmlFile = 'htmls/index.html'
        self.loginform = LoginWidget(params,path)
        if not ('content' in _params.keys()):
            _params['content'] = [{'name' : ['news']}]
        self.menu = MenuWidget(params,path,path)
        self.content = Widget.FromDictionary(params,path+'|content(0)');
        self.header = HeaderWidget(params,path,path)
        self.params = _params
