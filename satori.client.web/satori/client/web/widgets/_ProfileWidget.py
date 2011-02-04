from satori.client.web.queries import *
from satori.client.common import want_import
want_import(globals(), '*')
from _Widget import Widget

from docutils.core import publish_parts

# news table (a possible main content)
class ProfileWidget(Widget):
    pathName = 'profile'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/profile.html'
        d = follow(params,path)
        self.status = d.get('status','')
        if self.status:
            self.status = self.status[0]
            del d['status']
        self.exid_linked = []
        self.exid_ready = []
        self.back_to = ToString(params)
        self.back_path = path
        self.exid_linked = ExternalIdentity.get_linked()
        for s,o in ExternalIdentity.get_ready().items():
            o.salt = s;
            self.exid_ready.append(o)
