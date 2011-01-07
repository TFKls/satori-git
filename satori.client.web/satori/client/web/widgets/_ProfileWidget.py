from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

from docutils.core import publish_parts

# news table (a possible main content)
class ProfileWidget(Widget):
    pathName = 'profile'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/profile.html'
        self.exid_linked = []
        self.exid_ready = []
        self.exid_linked = ExternalIdentity.get_linked()
        for s,o in ExternalIdentity.get_ready().items():
            o.salt = s;
            self.exid_ready.append(o)
