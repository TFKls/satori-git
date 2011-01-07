from satori.client.web.URLDictionary import *
from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget
from django.conf import settings
from satori.client.web.librecaptcha import *

# register box
class RegisterWidget(Widget):
    pathName = 'registerform'
    def __init__(self, params, path):
        self.status = follow(params,path).get('status')
        if self.status:
            self.status = self.status[0]
        el = CurrentUser()
        if el:
            self.htmlFile = 'htmls/logged.html'
            self.name = el.name
        else:
            self.htmlFile = 'htmls/registerform.html'
            self.back_to = ToString(params)
            self.lw_path = path
            self.captchahtml = displayhtml(settings.RECAPTCHA_PUB_KEY,theme='white')
