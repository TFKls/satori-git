from satori.client.web.queries import *
from satori.client.common.remote import *
from _Widget import Widget

from docutils.core import publish_parts

# news table (a possible main content)
class IdentitiesWidget(Widget):
    pathName = 'identities'
    def __init__(self, params, path):
        self.htmlFile = 'htmls/identities.html'
        self.openid_linked = []
        self.openid_ready = []
        self.cas_linked = []
        self.cas_ready = []
        self.openid_linked = OpenIdentity.get_linked()
        for s,o in OpenIdentity.get_ready().items():
            o.salt = s;
            self.openid_ready.append(o)
        self.cas_linked = CentralAuthenticationService.get_linked()
        for s,o in CentralAuthenticationService.get_ready().items():
            o.salt = s;
            self.cas_ready.append(o)
